import os
import json
# from prompt import prompt,evaluator_agent_prompt
from pydub import AudioSegment
from pydub.playback import play
import io,re
from therapist.th_prompt import system_prompt, evaluator_agent_prompt,object_selector_agent_prompt,severe_aphasia_quesion_generator_prompt
import httpx
from utils import clean_json
import json
import re
from therapist. question_generator import QuestionGeneratorAgent
from therapist.phonetic_hint_agent import PhoneticHintAgent
from therapist.classifier_agent import ClassifierAgent
from therapist.utils import extract_json_from_response
from therapist.question_framing_agent import QuestionFramingAgent
from therapist.phoentic_critic import PhoneticValidatorAgent
from therapist.evaluator_agent import EvaluatorAgent
from therapist.descriptive_hint_agent import HintgeneratorAgent
from therapist.descriptive_criric import ValidatorAgent

question_agent=QuestionGeneratorAgent()
ph_hint=PhoneticHintAgent()
classif=ClassifierAgent()
evaluator=EvaluatorAgent()

question_framer=QuestionFramingAgent()
ph_critic=PhoneticValidatorAgent()
hint_agent=HintgeneratorAgent()
hint_v=ValidatorAgent()

class generate_therapist:
    def __init__(self):
        self.question_agent = question_agent
        self.question_framer=question_framer
        self.evaluator = evaluator
        self.classifier=classif
        self.hint_agent = hint_agent
        self.ph_hint=ph_hint
        self.url="http://localhost:7878/api/llm/generate"
    def _generatequestionlist(self, age,gender,lifestyle,location, profession, language,severity):
        raw_output = self.question_agent.generate_questions_for_severity(age,gender,lifestyle,location, profession, language,severity)
        object_list=(raw_output)["object_list"]
        question_list={}
        for q_no,obj in enumerate(object_list):
            question=self._generatequestion(object=obj,question_type="naming_from_description")
            question_list[f"q{q_no+1}"]=question
        return question_list
    
    def _testevaluator(self,object,question, q_type, user_response):
        evaluation_json = self.evaluator.evaluate_and_predict(object,question, q_type, user_response)
        print("evaleval")
        print(evaluation_json)
        evaluation = extract_json_from_response(evaluation_json)
        return evaluation
        
    def main(self,age,gender,lifestyle,location, profession, language,severity):
        questions=self._generatequestionlist(age,gender,lifestyle,location, profession, language,severity)
        return questions
    
    def _generatequestion(self,object,question_type):
        question = self.question_framer.frame_question_and_hint(object,question_type)
        image_url='http://static.flickr.com/2723/4385058960_b0f291553e.jpg'
        response={'object':object,'question':question,'question_type':question_type,'image':image_url}
        return response
    
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
        