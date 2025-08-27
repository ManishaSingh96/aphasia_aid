import os
import time
import json
import psutil
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

from pathlib import Path
from therapist.conversation_generator.question_generator import QuestionGeneratorAgent
from therapist.conversation_generator.phonetic_hint_agent import PhoneticHintAgent
from therapist.conversation_generator.classifier_agent import ClassifierAgent
from therapist.utils import extract_json_from_response
from therapist.conversation_generator.question_framing_agent import QuestionFramingAgent
from therapist.conversation_generator.phoentic_critic import PhoneticValidatorAgent
from therapist.conversation_generator.evaluator_agent import EvaluatorAgent
from therapist.conversation_generator.descriptive_hint_agent import HintgeneratorAgent
from therapist.conversation_generator.descriptive_criric import ValidatorAgent
from therapist.image_generator.image_generator import generate_image

# Agents initialization
question_agent = QuestionGeneratorAgent()
ph_hint = PhoneticHintAgent()
classif = ClassifierAgent()
evaluator = EvaluatorAgent()
question_framer = QuestionFramingAgent()
ph_critic = PhoneticValidatorAgent()
hint_agent = HintgeneratorAgent()
hint_v = ValidatorAgent()
BASE_DIR = Path(__file__).resolve().parent  # folder containing model.py
parquet_path = BASE_DIR / "image_generator" / "cc12m_7m_subset_translated.parquet"

df = pd.read_parquet(parquet_path) 
image_gen = generate_image(model='text-embedding-3-large', batch_size=200)

FALLBACK_IMAGE = "http://static.flickr.com/2723/4385058960_b0f291553e.jpg"
        
def _extract_object_name(obj):
    if isinstance(obj, dict):
        return obj.get("english") or next((v for v in obj.values() if isinstance(v, str) and v.strip()), "")
    return str(obj)


class generate_therapist:
    def __init__(self, profiling_log="profiling_metrics.json"):
        self.question_agent = question_agent
        self.question_framer = question_framer
        self.evaluator = evaluator
        self.classifier = classif
        self.hint_agent = hint_agent
        self.ph_hint = ph_hint
        self.image_gen = image_gen
        self.url = "http://localhost:7879/api/llm/generate"
        self.profiling_log = profiling_log
        self.metrics = {}

    def _log_step(self, step_name, start_time):
        """Log execution time & memory usage for each step"""
        elapsed = time.time() - start_time
        process = psutil.Process(os.getpid())
        mem_usage = process.memory_info().rss / (1024 ** 2)  # MB
        self.metrics[step_name] = {
            "time_sec": round(elapsed, 3),
            "memory_mb": round(mem_usage, 2)
        }

    def _save_metrics(self):
        """Save profiling data to JSON"""
        with open(self.profiling_log, "w") as f:
            json.dump(self.metrics, f, indent=4)
        print(f"[✓] Profiling data saved to {self.profiling_log}")

    def _generatequestion(self, object, question_type):
        start = time.time()
        question = self.question_framer.frame_question_and_hint(object, question_type)
        image_url = self.image_gen.generate_image(object,df) or FALLBACK_IMAGE
        self._log_step(f"generate_question_{object}", start)
        return {
            "object": object,
            "question": question,
            "question_type": question_type,
            "image": image_url
        }

    def _generatequestion_parallel_task(self, idx, object_name, question_type, retries=2, backoff=0.8):
        attempt, delay = 0, backoff
        while True:
            try:
                start = time.time()
                out = self._generatequestion(object_name, question_type)
                self._log_step(f"parallel_task_{idx}", start)
                return idx, out
            except Exception as e:
                attempt += 1
                if attempt > retries:
                    return idx, {
                        "object": object_name,
                        "question": None,
                        "question_type": question_type,
                        "image": FALLBACK_IMAGE,
                        "error": f"{type(e).__name__}: {e}",
                    }
                time.sleep(delay)
                delay *= 1.5

    def _generatequestionlist(self, age, gender, location, profession, language, severity,
                              question_type="naming_from_description", max_workers=20, retries=2):
        start = time.time()
        raw_output = self.question_agent.generate_questions_for_severity(
            age, gender, location, profession, language, severity
        )
        object_list = raw_output["object_list"]
        objs = [_extract_object_name(o) for o in object_list]

        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(self._generatequestion_parallel_task, i, obj, question_type, retries): i
                for i, obj in enumerate(objs)
            }
            for fut in tqdm(as_completed(futures), total=len(futures), desc="Generating questions"):
                i, payload = fut.result()
                results[i] = payload

        self._log_step("generate_question_list", start)
        return {f"q{i + 1}": results.get(i) for i in range(len(objs))}

    def main(self, age, gender, location, profession, language, severity):
        print("[✓] Generating full question set...")
        start = time.time()
        questions = self._generatequestionlist(age, gender, location, profession, language, severity)
        self._log_step("main_execution", start)
        self._save_metrics()
        return questions

    def _testevaluator(self, object):
        start = time.time()
        image_url = self.image_gen.generate_image(object,df) or FALLBACK_IMAGE
        self._log_step("test_evaluator", start)
        return image_url

    def evaluate(self, object, question, question_type, user_response, user_history, hint_reponse):
        start = time.time()
        obj = object
        q_type = question_type
        attempt = (max(user_history.keys()) if user_history else 0) + 1
        ph_hint_history = hint_reponse
        if len(ph_hint_history) < 1:
            ph_hint_history[attempt] = "no hint given till now"
        user_history[attempt] = user_response
        classifier_response = self.classifier.evaluate_and_predict(user_response)

        if classifier_response:
            ph_hint_response = self.ph_hint.generate_hint(obj, question, user_response, ph_hint_history, critic_feedback=None)
            attempt += 1
            ph_hint_history_copy = ph_hint_history.copy()
            ph_hint_history_copy[attempt] = ph_hint_response
            critic_response = ph_critic.validate(obj, ph_hint_history_copy, question, user_response)
            if not critic_response[0]:
                ph_hint_response = self.ph_hint.generate_hint(
                    obj, question, user_response,
                    ph_hint_history, ph_hint_response + ' is incorrect because ' + critic_response[1]
                )
            ph_hint_history[attempt] = ph_hint_response
            response = {'hint_history': ph_hint_history, 'user_history': user_history,
                        'hint': ph_hint_response, 'evaluation': "incorrect"}
        else:
            evaluation_json = self.evaluator.evaluate_and_predict(obj, question, q_type, user_response)
            evaluation = extract_json_from_response(evaluation_json)
            evaluation_result = evaluation.get('Evaluation', '').lower()
            eval_reason = evaluation.get('Reason', '').lower()

            if evaluation_result != 'correct':
                ph_hint_response = self.hint_agent.generate_hint(obj, question, user_response,
                                                                 eval_reason, ph_hint_history, critic_feedback=None)
                attempt += 1
                ph_hint_history_copy = ph_hint_history.copy()
                ph_hint_history_copy[attempt] = ph_hint_response
                critic_response = hint_v.validate(obj, ph_hint_history, question, user_response)
                if not critic_response[0]:
                    ph_hint_response = self.hint_agent.generate_hint(
                        obj, question, user_response,
                        eval_reason, ph_hint_history, ph_hint_response + ' is incorrect because ' + critic_response[1]
                    )
                ph_hint_history[attempt] = ph_hint_response
                response = {'hint_history': ph_hint_history, 'user_history': user_history,
                            'hint': ph_hint_response, 'evaluation': evaluation_result}
            else:
                ph_hint_response = self.hint_agent.generate_hint(obj, question, user_response,
                                                                 eval_reason, ph_hint_history, critic_feedback=None)
                response = {'hint_history': ph_hint_history, 'user_history': user_history,
                            'hint': ph_hint_response, 'evaluation': evaluation_result}

        self._log_step("evaluate", start)
        return response
