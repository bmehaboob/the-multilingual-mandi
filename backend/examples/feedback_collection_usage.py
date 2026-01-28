"""
Example usage of the feedback collection system.

This demonstrates how to use the feedback collection API endpoints
for continuous model improvement and user satisfaction tracking.

Requirements: 20.1, 20.2, 22.1, 22.3, 22.4
"""
import requests
from typing import Dict, Any
from uuid import UUID


class FeedbackClient:
    """Client for interacting with feedback collection API"""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def submit_transcription_correction(
        self,
        incorrect: str,
        correct: str,
        language: str,
        confidence_score: float = None,
        audio_hash: str = None
    ) -> Dict[str, Any]:
        """
        Submit a transcription correction for model improvement.
        
        Example:
            User hears: "टमाटर का भाव क्या है"
            System transcribed: "टमाटर का भाग क्या है" (wrong)
            User corrects it
        """
        data = {
            "incorrect_transcription": incorrect,
            "correct_transcription": correct,
            "language": language
        }
        
        if confidence_score is not None:
            data["confidence_score"] = confidence_score
        if audio_hash is not None:
            data["audio_hash"] = audio_hash
        
        response = requests.post(
            f"{self.base_url}/feedback/transcription-correction",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def submit_negotiation_feedback(
        self,
        rating: int,
        was_helpful: bool,
        was_culturally_appropriate: bool = None,
        was_used: bool = None,
        commodity: str = None,
        suggested_price: float = None,
        feedback_text: str = None
    ) -> Dict[str, Any]:
        """
        Submit feedback on negotiation suggestions.
        
        Example:
            Sauda Bot suggested: "भाई साहब, 25 रुपये में दे दीजिए"
            User found it helpful and culturally appropriate
        """
        data = {
            "rating": rating,
            "was_helpful": was_helpful
        }
        
        if was_culturally_appropriate is not None:
            data["was_culturally_appropriate"] = was_culturally_appropriate
        if was_used is not None:
            data["was_used"] = was_used
        if commodity is not None:
            data["commodity"] = commodity
        if suggested_price is not None:
            data["suggested_price"] = suggested_price
        if feedback_text is not None:
            data["feedback_text"] = feedback_text
        
        response = requests.post(
            f"{self.base_url}/feedback/negotiation",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def submit_satisfaction_survey(
        self,
        survey_type: str,
        overall_rating: str,
        language: str,
        voice_translation_rating: int = None,
        price_oracle_rating: int = None,
        negotiation_assistant_rating: int = None,
        price_oracle_helpful: bool = None,
        negotiation_suggestions_helpful: bool = None
    ) -> Dict[str, Any]:
        """
        Submit a satisfaction survey.
        
        Example:
            After a transaction, ask user:
            "How satisfied are you with your experience?"
            "Was the Price Oracle helpful?"
        """
        data = {
            "survey_type": survey_type,
            "overall_rating": overall_rating,
            "language": language
        }
        
        if voice_translation_rating is not None:
            data["voice_translation_rating"] = voice_translation_rating
        if price_oracle_rating is not None:
            data["price_oracle_rating"] = price_oracle_rating
        if negotiation_assistant_rating is not None:
            data["negotiation_assistant_rating"] = negotiation_assistant_rating
        if price_oracle_helpful is not None:
            data["price_oracle_helpful"] = price_oracle_helpful
        if negotiation_suggestions_helpful is not None:
            data["negotiation_suggestions_helpful"] = negotiation_suggestions_helpful
        
        response = requests.post(
            f"{self.base_url}/feedback/satisfaction-survey",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def submit_price_oracle_feedback(
        self,
        commodity: str,
        was_helpful: bool,
        quoted_price: float = None,
        market_average: float = None,
        price_verdict: str = None,
        influenced_decision: bool = None
    ) -> Dict[str, Any]:
        """
        Submit feedback on Price Oracle helpfulness.
        
        Example:
            After checking tomato prices:
            "Was the price information helpful?"
            "Did it influence your decision?"
        """
        data = {
            "commodity": commodity,
            "was_helpful": was_helpful
        }
        
        if quoted_price is not None:
            data["quoted_price"] = quoted_price
        if market_average is not None:
            data["market_average"] = market_average
        if price_verdict is not None:
            data["price_verdict"] = price_verdict
        if influenced_decision is not None:
            data["influenced_decision"] = influenced_decision
        
        response = requests.post(
            f"{self.base_url}/feedback/price-oracle",
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def initiate_voice_survey(
        self,
        survey_type: str,
        language: str,
        transaction_id: UUID = None
    ) -> Dict[str, Any]:
        """
        Initiate a voice-based survey and get prompts.
        
        Returns voice prompts that can be played to the user.
        """
        data = {
            "survey_type": survey_type,
            "language": language
        }
        
        if transaction_id is not None:
            data["transaction_id"] = str(transaction_id)
        
        response = requests.post(
            f"{self.base_url}/feedback/voice-survey/initiate",
            json=data,
            headers=self.headers
        )
        return response.json()


# Example Usage Scenarios

def example_1_transcription_correction():
    """
    Scenario: User corrects a transcription error
    
    Requirement 20.1: When a user corrects a transcription error,
    the platform shall log the original audio, incorrect transcription,
    and user correction.
    """
    client = FeedbackClient(
        base_url="http://localhost:8000/api/v1",
        auth_token="user_auth_token_here"
    )
    
    # User spoke: "टमाटर का भाव क्या है" (What is the price of tomatoes?)
    # System transcribed: "टमाटर का भाग क्या है" (wrong - भाग instead of भाव)
    # User corrects it
    
    result = client.submit_transcription_correction(
        incorrect="टमाटर का भाग क्या है",
        correct="टमाटर का भाव क्या है",
        language="hi",
        confidence_score=0.65,  # Low confidence triggered correction prompt
        audio_hash="abc123def456"  # Hash of the audio file
    )
    
    print("Transcription correction submitted:")
    print(f"  ID: {result['id']}")
    print(f"  Language: {result['language']}")
    print(f"  Confidence: {result['confidence_score']}")


def example_2_negotiation_feedback():
    """
    Scenario: User provides feedback on negotiation suggestion
    
    Requirement 22.4: When a negotiation concludes, the platform shall
    ask users if the Sauda Bot suggestions were culturally appropriate
    and useful.
    """
    client = FeedbackClient(
        base_url="http://localhost:8000/api/v1",
        auth_token="user_auth_token_here"
    )
    
    # Sauda Bot suggested: "भाई साहब, 25 रुपये में दे दीजिए"
    # (Brother, please give it for 25 rupees)
    # User found it helpful and used it
    
    result = client.submit_negotiation_feedback(
        rating=5,
        was_helpful=True,
        was_culturally_appropriate=True,
        was_used=True,
        commodity="tomato",
        suggested_price=25.0,
        feedback_text="The suggestion was polite and effective"
    )
    
    print("Negotiation feedback submitted:")
    print(f"  Rating: {result['rating']}/5")
    print(f"  Helpful: {result['was_helpful']}")
    print(f"  Culturally appropriate: {result['was_culturally_appropriate']}")


def example_3_post_transaction_survey():
    """
    Scenario: Conduct post-transaction satisfaction survey
    
    Requirements 22.1, 22.3: The platform shall conduct periodic
    voice-based satisfaction surveys and ask if Fair Price Oracle
    was helpful.
    """
    client = FeedbackClient(
        base_url="http://localhost:8000/api/v1",
        auth_token="user_auth_token_here"
    )
    
    # After completing a transaction, ask user for feedback
    result = client.submit_satisfaction_survey(
        survey_type="post_transaction",
        overall_rating="satisfied",
        language="hi",
        voice_translation_rating=5,
        price_oracle_rating=4,
        negotiation_assistant_rating=5,
        price_oracle_helpful=True,
        negotiation_suggestions_helpful=True
    )
    
    print("Satisfaction survey submitted:")
    print(f"  Overall: {result['overall_rating']}")
    print(f"  Voice translation: {result['voice_translation_rating']}/5")
    print(f"  Price oracle: {result['price_oracle_rating']}/5")


def example_4_price_oracle_feedback():
    """
    Scenario: User provides feedback on Price Oracle
    
    Requirement 22.3: When a transaction is completed, the platform
    shall ask users if they found the Fair Price Oracle helpful.
    """
    client = FeedbackClient(
        base_url="http://localhost:8000/api/v1",
        auth_token="user_auth_token_here"
    )
    
    # User checked tomato prices before buying
    # Seller quoted 30 Rs/kg, market average was 25 Rs/kg
    # Price Oracle said "high" - user found it helpful
    
    result = client.submit_price_oracle_feedback(
        commodity="tomato",
        was_helpful=True,
        quoted_price=30.0,
        market_average=25.0,
        price_verdict="high",
        influenced_decision=True
    )
    
    print("Price Oracle feedback submitted:")
    print(f"  Commodity: {result['commodity']}")
    print(f"  Helpful: {result['was_helpful']}")
    print(f"  Influenced decision: {result['influenced_decision']}")


def example_5_voice_survey_flow():
    """
    Scenario: Conduct a voice-based survey
    
    Requirement 22.1: The platform shall conduct periodic voice-based
    satisfaction surveys asking users to rate their experience.
    """
    client = FeedbackClient(
        base_url="http://localhost:8000/api/v1",
        auth_token="user_auth_token_here"
    )
    
    # Step 1: Initiate survey and get voice prompts
    prompt = client.initiate_voice_survey(
        survey_type="periodic",
        language="hi"
    )
    
    print("Voice survey initiated:")
    print(f"  Prompt: {prompt['prompt_text']}")
    print(f"  Expected response: {prompt['expected_response_type']}")
    print(f"  Options: {prompt.get('options', [])}")
    
    # Step 2: Play prompt to user via TTS
    # Step 3: Capture user's voice response
    # Step 4: Transcribe response
    # Step 5: Submit survey with transcribed responses
    
    # (In a real implementation, this would be a multi-step flow)


def example_6_continuous_improvement_pipeline():
    """
    Scenario: Using feedback for continuous model improvement
    
    Requirement 20.3: When sufficient correction data is accumulated,
    the platform shall retrain or fine-tune STT models for improved
    accuracy.
    """
    # This example shows how feedback data can be used for model improvement
    
    # 1. Collect transcription corrections over time
    corrections = [
        {"incorrect": "टमाटर का भाग", "correct": "टमाटर का भाव", "language": "hi"},
        {"incorrect": "प्याज का दाम", "correct": "प्याज का दाम", "language": "hi"},
        # ... more corrections
    ]
    
    # 2. Analyze correction patterns
    # - Identify common errors (e.g., भाग vs भाव confusion)
    # - Group by language and dialect
    # - Prioritize low-resource dialects
    
    # 3. Prepare training data
    # - Create correction pairs for fine-tuning
    # - Add domain-specific vocabulary
    
    # 4. Fine-tune models
    # - Use corrections to improve STT accuracy
    # - Test on validation set
    # - Deploy improved model
    
    # 5. Measure improvement
    # - Track correction rates before/after
    # - Monitor user satisfaction scores
    
    print("Continuous improvement pipeline:")
    print("  1. Collect feedback ✓")
    print("  2. Analyze patterns")
    print("  3. Prepare training data")
    print("  4. Fine-tune models")
    print("  5. Deploy and measure")


if __name__ == "__main__":
    print("=== Feedback Collection System Examples ===\n")
    
    print("Example 1: Transcription Correction")
    print("-" * 50)
    # example_1_transcription_correction()
    print("(Commented out - requires running server)\n")
    
    print("Example 2: Negotiation Feedback")
    print("-" * 50)
    # example_2_negotiation_feedback()
    print("(Commented out - requires running server)\n")
    
    print("Example 3: Post-Transaction Survey")
    print("-" * 50)
    # example_3_post_transaction_survey()
    print("(Commented out - requires running server)\n")
    
    print("Example 4: Price Oracle Feedback")
    print("-" * 50)
    # example_4_price_oracle_feedback()
    print("(Commented out - requires running server)\n")
    
    print("Example 5: Voice Survey Flow")
    print("-" * 50)
    # example_5_voice_survey_flow()
    print("(Commented out - requires running server)\n")
    
    print("Example 6: Continuous Improvement Pipeline")
    print("-" * 50)
    example_6_continuous_improvement_pipeline()
    print()
    
    print("\nTo run these examples:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. Authenticate and get a token")
    print("3. Uncomment the example functions above")
    print("4. Run this script: python examples/feedback_collection_usage.py")
