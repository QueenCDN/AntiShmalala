import google.generativeai as genai
import config
import texts
import logging

logger = logging.getLogger(__name__)

genai.configure(api_key=config.GEMINI_API_KEY)

async def get_gemini_response(prompt: str) -> str:
    """Получает ответ от Gemini на основе промпта, используя системный промпт Шмы."""
    try:
        shma_model = genai.GenerativeModel(
            config.GEMINI_MODEL_NAME,
            system_instruction=config.GEMINI_SYSTEM_PROMPT
        )
        response = await shma_model.generate_content_async(prompt)
        
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Gemini prompt blocked for general response: {response.prompt_feedback.block_reason_message}")
            return "Пф, даже отвечать на это не хочу. Скукота." 
        if response.candidates and response.candidates[0].finish_reason != 1: 
             logger.warning(f"Gemini generation finished with reason: {response.candidates[0].finish_reason}")
             if response.candidates[0].finish_reason in [genai.types.FinishReason.SAFETY, genai.types.FinishReason.RECITATION]:
                return "Мои темные силы говорят, что на такое я отвечать не буду. Попробуй что-нибудь менее убогое." 
        
        if not response.text.strip():
            logger.warning("Gemini returned an empty response, possibly due to safety filters or other issues.")
            return "Заткнись. Я не в настроении." 

        return response.text
    except Exception as e:
        logger.error(f"Error communicating with Gemini for general response: {e}")
        return texts.ERROR_GEMINI_MSG # Общая ошибка

async def get_gemini_joke() -> str:
    """Просит Gemini придумать анекдот, используя системный промпт Шмы."""
    try:
        shma_model = genai.GenerativeModel(
            config.GEMINI_MODEL_NAME,
            system_instruction=config.GEMINI_SYSTEM_PROMPT
        )
        response = await shma_model.generate_content_async("Расскажи анекдот.")
        
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Gemini joke prompt blocked: {response.prompt_feedback.block_reason_message}")
            return "Анекдоты? Сегодня не в настроении смешить таких, как ты. Отвали."
        if response.candidates and response.candidates[0].finish_reason != 1:
             logger.warning(f"Gemini joke generation finished with reason: {response.candidates[0].finish_reason}")
             if response.candidates[0].finish_reason in [genai.types.FinishReason.SAFETY, genai.types.FinishReason.RECITATION]:
                return "Мой юмор слишком черен для твоих жалких ушей. Проваливай."
        
        if not response.text.strip():
            logger.warning("Gemini returned an empty joke.")
            return "Анекдот застрял у меня в горле. Как и ты."

        return response.text
    except Exception as e:
        logger.error(f"Error getting joke from Gemini: {e}")
        return texts.ERROR_JOKE_MSG

async def get_truth_question() -> str | None:
    """Просит Gemini придумать вопрос для "Правды"."""
    prompt_for_truth = "Сыграем в Правду или Действие. Я выбираю Правду. Задай мне вопрос."
    try:
        shma_model = genai.GenerativeModel(
            config.GEMINI_MODEL_NAME,
            system_instruction=config.GEMINI_SYSTEM_PROMPT # Используем личность Шмы
        )
        response = await shma_model.generate_content_async(prompt_for_truth)

        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Gemini truth prompt blocked: {response.prompt_feedback.block_reason_message}")
            return None
        if response.candidates and response.candidates[0].finish_reason != 1:
             logger.warning(f"Gemini truth generation finished with reason: {response.candidates[0].finish_reason}")
             return None
        
        if not response.text.strip():
            logger.warning("Gemini returned an empty truth question.")
            return None

        # Gemini должен вернуть только вопрос, согласно обновленному системному промпту
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error getting truth question from Gemini: {e}")
    return None


async def get_dare_task() -> str:
    """Просит Gemini придумать задание для "Действия"."""
    prompt_for_dare = "Сыграем в Правду или Действие. Я выбираю Действие. Придумай мне задание."
    try:
        shma_model = genai.GenerativeModel(
            config.GEMINI_MODEL_NAME,
            system_instruction=config.GEMINI_SYSTEM_PROMPT 
        )
        response = await shma_model.generate_content_async(prompt_for_dare)

        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Gemini dare prompt blocked: {response.prompt_feedback.block_reason_message}")
            return texts.ERROR_DARE_MSG # Общая ошибка, можно заменить на ответ в стиле Шмы
        if response.candidates and response.candidates[0].finish_reason != 1:
             logger.warning(f"Gemini dare generation finished with reason: {response.candidates[0].finish_reason}")
             return texts.ERROR_DARE_MSG 
        
        if not response.text.strip():
            logger.warning("Gemini returned an empty dare task.")
            return "Не могу придумать ничего достаточно унизительного для тебя. Повезло."


        return response.text.strip()
    except Exception as e:
        logger.error(f"Error getting dare from Gemini: {e}")
        return texts.ERROR_DARE_MSG