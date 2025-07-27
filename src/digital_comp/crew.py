from crewai import Agent, Crew, Task, LLM
from crewai.project import CrewBase, agent, task
from langchain_community.llms import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Setup
llm = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.0
)

@CrewBase
class SchemeAndDocumentCrew:

    # ---------- AGENTS ----------
    @agent
    def intent_detector(self) -> Agent:
        return Agent(
            config=self.agents_config['intent_detector'],
            llm=llm
        )

    @agent
    def smart_schemer(self) -> Agent:
        return Agent(
            config=self.agents_config['smart_schemer'],
            llm=llm
        )

    @agent
    def fraud_expert(self) -> Agent:
        return Agent(
            config=self.agents_config['fraud_expert'],
            llm=llm
        )

    @agent
    def document_checker(self) -> Agent:
        return Agent(
            config=self.agents_config['document_checker'],
            llm=llm
        )

    # ---------- TASKS ----------
    @task
    def document_validation_task(self) -> Task:
        return Task(
            description="Validate the uploaded documents against the scheme requirements. Use {scheme_info} and {documents_info} provided as inputs.Ensure that you check against all required documents for the scheme.",
            expected_output="A table showing for each required document: its type, whether it is present, whether it is valid, and any notes.Identify the language used in {scheme_info} and give output in same language in appropriate script",
            agent=self.document_checker(),
            llm=llm
        )

    # ---------- FLOWS ----------

    # Step 1: Detect intent from user query
    def detect_intent(self, user_query: str):
        print("👂 Received Query:", user_query)
        intent_task = Task(
            description=f"Detect intent from this query: {user_query}",
            expected_output="Return either 'fraud' or 'scheme'",
            agent=self.intent_detector(),
            llm=llm
        )

        crew = Crew(agents=[self.intent_detector()], tasks=[intent_task])
        result = crew.kickoff({"user_query": user_query})

        try:
            intent_value = result.raw or result.task_outputs[0].raw
            print("🎯 Extracted intent:", intent_value)
            return intent_value.lower().strip()
        except Exception as e:
            raise ValueError(f"❌ Failed to extract intent from CrewOutput. Error: {e}")

    # Step 2: Route task based on intent
    def get_final_task(self, intent: str, query: str) -> Task:
        if "fraud" in intent:
            return Task(
                description=(
                    f"Provide fraud safety advice for: '{query}', in the same language and appropriate script as the query.\n\n"
                    "Only give useful and easy-to-understand safety tips. Do not include disclaimers like 'I cannot guarantee...'. "
                    "Focus on how users can protect themselves from financial scams, phishing, digital fraud, etc."
                ),
                expected_output="Clear and helpful list of fraud prevention tips.",
                agent=self.fraud_expert(),
                llm=llm
            )
        else:
            return Task(
                description=(
                    f"Provide comprehensive and helpful information for Indian government scheme(s) relevant to: '{query}', "
                    f"responding in the same language and script as used in the query.\n\n"
                    "Your answer must be accurate, actionable, and detailed. Do not include generic disclaimers like 'I cannot provide all schemes' or 'this varies'. "
                    "Instead, focus on the most relevant central or state schemes based on the query context, and present the information clearly.\n\n"
                    "For each scheme, include the following structured details with as much explanation as possible:\n\n"
                    "Scheme Name: <Name of the scheme>\n"
                    "Eligibility: <Who can apply, including income, age, location, category, etc.>\n"
                    "Benefits: <What the user will receive or gain from the scheme>\n"
                    "Required Documents: <List of important documents needed to apply>\n"
                    "How to Apply: <Where and how to apply — online portal, offline center, CSC, etc.>\n"
                    "Application Link or Portal (if available): <URL or mention official site>\n"
                    "Valid Till / Timeline (if applicable): <Deadline, if any>\n\n"
                    "If any urgent deadlines, time-sensitive actions, or document reminders exist, include the following at the end:\n"
                    "REMINDER: ⚠ <Your reminder message here>\n\n"
                    "Respond in clean, easy-to-read format. Do not include extra commentary or limitations. Your goal is to help the user take immediate action."
                    "Detect the language and script used in the input query and respond in the *same language and script*. Do not use English unless the query was in English.\n\n"

                ),
                expected_output="Clean text with scheme details and optional REMINDER at the end.",
                agent=self.smart_schemer(),
                llm=llm
            )


    # 🚀 Method for text query flow
    def run_scheme_or_fraud_flow(self, user_query: str):
        intent = self.detect_intent(user_query)
        print("🔍 Detected Intent:", intent)
        final_task = self.get_final_task(intent, user_query)
        crew = Crew(tasks=[final_task])
        return crew.kickoff({"user_query": user_query})

    # 🚀 Method for document validation flow
    def run_document_validation_flow(self, scheme_info: str, documents_info: list):
        task = self.document_validation_task()
        crew = Crew(tasks=[task])
        return crew.kickoff({
            "scheme_info": scheme_info,
            "documents_info": documents_info
        })