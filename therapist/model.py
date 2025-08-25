import os
import time
import json
from tqdm import tqdm
from pydub import AudioSegment
from pydub.playback import play
import io,re
import httpx
from utils import clean_json
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import pandas as pd
from therapist. conversation_generator.question_generator import QuestionGeneratorAgent
from therapist. conversation_generator.phonetic_hint_agent import PhoneticHintAgent
from therapist. conversation_generator.classifier_agent import ClassifierAgent
from therapist.utils import extract_json_from_response
from therapist. conversation_generator.question_framing_agent import QuestionFramingAgent
from therapist. conversation_generator.phoentic_critic import PhoneticValidatorAgent
from therapist. conversation_generator.evaluator_agent import EvaluatorAgent
from therapist. conversation_generator.descriptive_hint_agent import HintgeneratorAgent
from therapist. conversation_generator.descriptive_criric import ValidatorAgent
from therapist.image_generator.image_generator import generate_image

question_agent=QuestionGeneratorAgent()
ph_hint=PhoneticHintAgent()
classif=ClassifierAgent()
evaluator=EvaluatorAgent()

question_framer=QuestionFramingAgent()
ph_critic=PhoneticValidatorAgent()
hint_agent=HintgeneratorAgent()
hint_v=ValidatorAgent()

image_gen=generate_image(model='text-embedding-3-large',batch_size=200)
FALLBACK_IMAGE = "http://static.flickr.com/2723/4385058960_b0f291553e.jpg"

def _extract_object_name(obj):
    """Accepts either 'apple' or {'english':'apple', ...} and returns a string."""
    if isinstance(obj, dict):
        return obj.get("english") or next(
            (v for v in obj.values() if isinstance(v, str) and v.strip()), ""
        )
    return str(obj)

class generate_therapist:
    def __init__(self):
        self.question_agent = question_agent
        self.question_framer=question_framer
        self.evaluator = evaluator
        self.classifier=classif
        self.hint_agent = hint_agent
        self.ph_hint=ph_hint
        self.image_gen=image_gen
        self.url="http://localhost:7878/api/llm/generate"


    def _generatequestion(self, object, question_type):
        question = self.question_framer.frame_question_and_hint(object, question_type)
        image_url = self.image_gen.generate_image(object) or FALLBACK_IMAGE
        # image_url = FALLBACK_IMAGE
        return {
        "object": object,
        "question": question,
        "question_type": question_type,
        "image": image_url
        }

    def _generatequestionlist(self, age, gender, location, profession, language, severity,
                              question_type="naming_from_description", max_workers=16, retries=2):
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

            return {f"q{i + 1}": results.get(i) for i in range(len(objs))}

    def main(self, age, gender, location, profession, language, severity):
        print("[✓] Generating full question set...")
        start_time = time.time()
        questions = self._generatequestionlist(age, gender, location, profession, language, severity)
        total_time = time.time() - start_time
        print(f"[✓] Completed all questions in {total_time:.2f} seconds")
        return questions

    def _generatequestionlist(self, age,gender,location, profession, language,severity):
        raw_output = self.question_agent.generate_questions_for_severity(age,gender,location, profession, language,severity)
        object_list=(raw_output)["object_list"]
        question_list={}
        for q_no,obj in enumerate(object_list):
            question=self._generatequestion(object=obj,question_type="naming_from_description")
            question_list[f"q{q_no+1}"]=question
        return question_list

    
    def _testevaluator(self,object):
        image_url=self.image_gen.generate_image(object)
        if not image_url:
            image_url='http://static.flickr.com/2723/4385058960_b0f291553e.jpg'
        return image_url
        
    def main(self,age,gender,location, profession, language,severity):
        questions=self._generatequestionlist(age,gender,location, profession, language,severity)
        return questions
    
    def evaluate(self,object,question,question_type,user_response,user_history,hint_reponse,):
        obj = object
        q_type=question_type
        print(user_history)
        attempt = (max(user_history.keys()) if user_history else 0) + 1
        ph_hint_history=hint_reponse
        if len(ph_hint_history)<1:
            ph_hint_history[attempt]="no hint given till now"
        user_history[attempt]=user_response
        classifier_response=self.classifier.evaluate_and_predict(user_response)
        if classifier_response: #gibbe
            ph_hint_response=self.ph_hint.generate_hint(obj,question,user_response,ph_hint_history,critic_feedback=None)
            attempt=attempt+1
            ph_hint_history_copy=ph_hint_history.copy()
            ph_hint_history_copy[attempt]=ph_hint_response
            critic_response=ph_critic.validate(obj,ph_hint_history_copy,question,user_response)
            if critic_response[0]:
                ph_hint_response=ph_hint_response
            else:
                ph_hint_response=self.ph_hint.generate_hint(obj,question,user_response,ph_hint_history,ph_hint_response + 'is incorrect because ' + critic_response[1])
                ph_hint_history[attempt]=ph_hint_response
            response={'hint_history':ph_hint_history, 'user_history':user_history,'hint':ph_hint_response,'evaluation':"incorrect"}
        else:
            evaluation_json = self.evaluator.evaluate_and_predict(obj,question, q_type, user_response)

            evaluation = extract_json_from_response(evaluation_json)
            evaluation_result = evaluation.get('Evaluation', '').lower()
            eval_reason=evaluation.get('Reason', '').lower()

            if evaluation_result!='correct':
                ph_hint_response = self.hint_agent.generate_hint(obj,question,user_response,eval_reason,ph_hint_history,critic_feedback=None)
                attempt=attempt+1
                ph_hint_history_copy=ph_hint_history.copy()
                ph_hint_history_copy[attempt]=ph_hint_response
                critic_response=hint_v.validate(obj,ph_hint_history,question,user_response)

                if critic_response[0]:
                    ph_hint_response=ph_hint_response
                else:
                    ph_hint_response=self.hint_agent.generate_hint(obj,question,user_response,eval_reason,ph_hint_history,ph_hint_response + 'is incorrect because ' + critic_response[1])
                ph_hint_history[attempt]=ph_hint_response
                response={'hint_history':ph_hint_history, 'user_history':user_history,'hint':ph_hint_response,'evaluation':evaluation_result}
            elif evaluation_result == 'correct':
                ph_hint_response = self.hint_agent.generate_hint(obj,question,user_response,eval_reason,ph_hint_history,critic_feedback=None)

                response={'hint_history':ph_hint_history, 'user_history':user_history,'hint':ph_hint_response,'evaluation':evaluation_result}
        return response
        