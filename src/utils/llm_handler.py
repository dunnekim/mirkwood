import os
from openai import OpenAI
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class LLMHandler:
    def __init__(self):
        # 안정적인 OpenAI 단일 클라이언트 사용
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def call_llm(self, system_prompt, user_prompt, mode="smart"):
        """
        LLM 호출 라우터 (GPT-4o-mini 통합)
        :param mode: 'fast'든 'smart'든 가성비 최강인 4o-mini 사용
        """
        try:
            # 4o-mini는 속도(Flash급)와 지능(3.5 이상)을 모두 갖춤
            model_name = "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3, # Fact 위주
                max_tokens=3000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"   ⚠️ LLM Error ({model_name}): {e}")
            return "{}" # 에러 시 빈 JSON 반환으로 시스템 다운 방지