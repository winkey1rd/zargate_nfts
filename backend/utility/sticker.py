from nft.config import ATTRIBUTE_GROUPS, EMOTIONS
from backend.utility.converter import get_key_by_values


def get_group_by_trait_type(trait_type: str) -> str | None:
    return get_key_by_values(trait_type, ATTRIBUTE_GROUPS)

def get_attr_num_by_emo_trait(emotion: str, trait_type: str) -> str | None:
    try:
        num = EMOTIONS.get(emotion).index(trait_type)
    except Exception as e:
        return None
    return str(num + 1)

def get_emotion_by_name(emotion_name: str) -> str | None:
    for emotion in EMOTIONS:
        if emotion in emotion_name:
            return emotion
    return None