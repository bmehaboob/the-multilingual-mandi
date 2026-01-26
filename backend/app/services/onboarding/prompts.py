"""Voice prompts for onboarding in multiple languages"""
from typing import Dict
from .models import OnboardingStep


# Voice prompts for each step in multiple languages
# Format: {language_code: {step: prompt_text}}
ONBOARDING_PROMPTS: Dict[str, Dict[OnboardingStep, str]] = {
    # Hindi prompts
    "hin": {
        OnboardingStep.WELCOME: "नमस्ते! मल्टीलिंगुअल मंडी में आपका स्वागत है। मैं आपको पंजीकरण में मदद करूंगा।",
        OnboardingStep.LANGUAGE_CONFIRMATION: "क्या आप हिंदी में जारी रखना चाहते हैं? कृपया हां या नहीं कहें।",
        OnboardingStep.COLLECT_NAME: "कृपया अपना नाम बताएं।",
        OnboardingStep.COLLECT_LOCATION: "कृपया अपना स्थान बताएं - राज्य और जिला।",
        OnboardingStep.COLLECT_PHONE: "कृपया अपना मोबाइल नंबर बताएं।",
        OnboardingStep.EXPLAIN_DATA_USAGE: "हम आपका नाम, स्थान और आवाज़ का डेटा सुरक्षित रखेंगे। यह केवल आपकी पहचान और बेहतर सेवा के लिए उपयोग होगा। आपका डेटा तीसरे पक्ष के साथ साझा नहीं किया जाएगा।",
        OnboardingStep.COLLECT_CONSENT: "क्या आप इस डेटा उपयोग के लिए सहमत हैं? कृपया हां या नहीं कहें।",
        OnboardingStep.CREATE_VOICEPRINT: "अब मैं आपकी आवाज़ की पहचान बनाऊंगा। कृपया निम्नलिखित वाक्य तीन बार बोलें: मेरा नाम {name} है और मैं {location} से हूं।",
        OnboardingStep.TUTORIAL: "पंजीकरण पूर्ण! आप अब कीमतें जांच सकते हैं, व्यापारियों से बात कर सकते हैं, और सौदा बॉट से मदद ले सकते हैं। क्या आप ट्यूटोरियल सुनना चाहते हैं?",
        OnboardingStep.COMPLETE: "धन्यवाद! आपका खाता तैयार है। शुभकामनाएं!"
    },
    # English prompts
    "eng": {
        OnboardingStep.WELCOME: "Hello! Welcome to Multilingual Mandi. I will help you register.",
        OnboardingStep.LANGUAGE_CONFIRMATION: "Would you like to continue in English? Please say yes or no.",
        OnboardingStep.COLLECT_NAME: "Please tell me your name.",
        OnboardingStep.COLLECT_LOCATION: "Please tell me your location - state and district.",
        OnboardingStep.COLLECT_PHONE: "Please tell me your mobile number.",
        OnboardingStep.EXPLAIN_DATA_USAGE: "We will securely store your name, location, and voice data. This will only be used for your identification and better service. Your data will not be shared with third parties.",
        OnboardingStep.COLLECT_CONSENT: "Do you agree to this data usage? Please say yes or no.",
        OnboardingStep.CREATE_VOICEPRINT: "Now I will create your voice profile. Please say the following sentence three times: My name is {name} and I am from {location}.",
        OnboardingStep.TUTORIAL: "Registration complete! You can now check prices, talk to traders, and get help from Sauda Bot. Would you like to hear a tutorial?",
        OnboardingStep.COMPLETE: "Thank you! Your account is ready. Best wishes!"
    },
    # Telugu prompts
    "tel": {
        OnboardingStep.WELCOME: "నమస్కారం! మల్టీలింగ్వల్ మండికి స్వాగతం. నేను మీకు రిజిస్ట్రేషన్‌లో సహాయం చేస్తాను.",
        OnboardingStep.LANGUAGE_CONFIRMATION: "మీరు తెలుగులో కొనసాగించాలనుకుంటున్నారా? దయచేసి అవును లేదా కాదు అని చెప్పండి.",
        OnboardingStep.COLLECT_NAME: "దయచేసి మీ పేరు చెప్పండి.",
        OnboardingStep.COLLECT_LOCATION: "దయచేసి మీ స్థానం చెప్పండి - రాష్ట్రం మరియు జిల్లా.",
        OnboardingStep.COLLECT_PHONE: "దయచేసి మీ మొబైల్ నంబర్ చెప్పండి.",
        OnboardingStep.EXPLAIN_DATA_USAGE: "మేము మీ పేరు, స్థానం మరియు వాయిస్ డేటాను సురక్షితంగా నిల్వ చేస్తాము. ఇది మీ గుర్తింపు మరియు మెరుగైన సేవ కోసం మాత్రమే ఉపయోగించబడుతుంది. మీ డేటా మూడవ పక్షాలతో భాగస్వామ్యం చేయబడదు.",
        OnboardingStep.COLLECT_CONSENT: "మీరు ఈ డేటా వినియోగానికి అంగీకరిస్తున్నారా? దయచేసి అవును లేదా కాదు అని చెప్పండి.",
        OnboardingStep.CREATE_VOICEPRINT: "ఇప్పుడు నేను మీ వాయిస్ ప్రొఫైల్‌ను సృష్టిస్తాను. దయచేసి ఈ వాక్యాన్ని మూడు సార్లు చెప్పండి: నా పేరు {name} మరియు నేను {location} నుండి వచ్చాను.",
        OnboardingStep.TUTORIAL: "రిజిస్ట్రేషన్ పూర్తయింది! మీరు ఇప్పుడు ధరలను తనిఖీ చేయవచ్చు, వ్యాపారులతో మాట్లాడవచ్చు మరియు సౌదా బాట్ నుండి సహాయం పొందవచ్చు. మీరు ట్యుటోరియల్ వినాలనుకుంటున్నారా?",
        OnboardingStep.COMPLETE: "ధన్యవాదాలు! మీ ఖాతా సిద్ధంగా ఉంది. శుభాకాంక్షలు!"
    },
    # Tamil prompts
    "tam": {
        OnboardingStep.WELCOME: "வணக்கம்! பன்மொழி மண்டிக்கு வரவேற்கிறோம். நான் உங்களுக்கு பதிவு செய்ய உதவுவேன்.",
        OnboardingStep.LANGUAGE_CONFIRMATION: "தமிழில் தொடர விரும்புகிறீர்களா? தயவுசெய்து ஆம் அல்லது இல்லை என்று சொல்லுங்கள்.",
        OnboardingStep.COLLECT_NAME: "தயவுசெய்து உங்கள் பெயரைச் சொல்லுங்கள்.",
        OnboardingStep.COLLECT_LOCATION: "தயவுசெய்து உங்கள் இடத்தைச் சொல்லுங்கள் - மாநிலம் மற்றும் மாவட்டம்.",
        OnboardingStep.COLLECT_PHONE: "தயவுசெய்து உங்கள் மொபைல் எண்ணைச் சொல்லுங்கள்.",
        OnboardingStep.EXPLAIN_DATA_USAGE: "உங்கள் பெயர், இடம் மற்றும் குரல் தரவை நாங்கள் பாதுகாப்பாக சேமிப்போம். இது உங்கள் அடையாளம் மற்றும் சிறந்த சேவைக்காக மட்டுமே பயன்படுத்தப்படும். உங்கள் தரவு மூன்றாம் தரப்பினருடன் பகிரப்படாது.",
        OnboardingStep.COLLECT_CONSENT: "இந்த தரவு பயன்பாட்டிற்கு நீங்கள் ஒப்புக்கொள்கிறீர்களா? தயவுசெய்து ஆம் அல்லது இல்லை என்று சொல்லுங்கள்.",
        OnboardingStep.CREATE_VOICEPRINT: "இப்போது நான் உங்கள் குரல் சுயவிவரத்தை உருவாக்குவேன். தயவுசெய்து பின்வரும் வாக்கியத்தை மூன்று முறை சொல்லுங்கள்: என் பெயர் {name} மற்றும் நான் {location} இலிருந்து வருகிறேன்.",
        OnboardingStep.TUTORIAL: "பதிவு முடிந்தது! நீங்கள் இப்போது விலைகளை சரிபார்க்கலாம், வர்த்தகர்களுடன் பேசலாம் மற்றும் சௌதா போட்டிலிருந்து உதவி பெறலாம். நீங்கள் பயிற்சியைக் கேட்க விரும்புகிறீர்களா?",
        OnboardingStep.COMPLETE: "நன்றி! உங்கள் கணக்கு தயார். வாழ்த்துக்கள்!"
    }
}


def get_prompt(language: str, step: OnboardingStep, **kwargs) -> str:
    """
    Get the voice prompt for a specific step and language.
    
    Args:
        language: ISO 639-3 language code
        step: The onboarding step
        **kwargs: Variables to format into the prompt (e.g., name, location)
    
    Returns:
        Formatted prompt text in the specified language
    """
    # Default to Hindi if language not supported
    if language not in ONBOARDING_PROMPTS:
        language = "hin"
    
    prompt_template = ONBOARDING_PROMPTS[language].get(step, "")
    
    # Format the prompt with any provided variables
    try:
        return prompt_template.format(**kwargs)
    except KeyError:
        # If formatting fails, return the template as-is
        return prompt_template


def get_supported_languages() -> list:
    """Get list of supported languages for onboarding"""
    return list(ONBOARDING_PROMPTS.keys())
