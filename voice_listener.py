"""
Prometheus Voice Listener
Sistema de reconhecimento de voz para comandos
"""

import os
import time
import yaml
from typing import Optional
from skills.logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")

# Importação condicional do speech_recognition
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("Biblioteca speech_recognition não instalada. Instale com: pip install SpeechRecognition pyaudio")


class VoiceListener:
    """
    Classe para captura e reconhecimento de comandos de voz
    """

    def __init__(self, config_file: str = "prometheus.yaml"):
        """
        Inicializa o listener de voz

        Args:
            config_file: Caminho para arquivo de configuração
        """
        self.config = self._load_config(config_file)
        self.recognizer = None
        self.microphone = None
        self.enabled = self.config.get("voice", {}).get("enabled", True)

        if SPEECH_RECOGNITION_AVAILABLE and self.enabled:
            self._setup_recognizer()
        else:
            logger.warning("Reconhecimento de voz desabilitado ou biblioteca não disponível")

    def _load_config(self, config_file: str) -> dict:
        """Carrega configurações do arquivo YAML"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                logger.warning(f"Arquivo de config não encontrado: {config_file}")
                return {}
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return {}

    def _setup_recognizer(self):
        """Configura o reconhecedor de voz"""
        try:
            self.recognizer = sr.Recognizer()

            voice_config = self.config.get("voice", {})
            self.recognizer.energy_threshold = voice_config.get("energy_threshold", 300)
            self.recognizer.pause_threshold = voice_config.get("pause_threshold", 0.8)

            # Tentar inicializar microfone
            try:
                self.microphone = sr.Microphone()
                logger.info("Microfone inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar microfone: {e}")
                self.microphone = None

        except Exception as e:
            logger.error(f"Erro ao configurar recognizer: {e}")

    def listen_once(self, timeout: int = 5) -> Optional[str]:
        """
        Escuta por um comando de voz

        Args:
            timeout: Tempo máximo de espera em segundos

        Returns:
            Texto reconhecido ou None
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.error("Speech recognition não disponível")
            return None

        if not self.enabled:
            logger.warning("Voice listener está desabilitado")
            return None

        if not self.microphone:
            logger.error("Microfone não disponível")
            return None

        try:
            logger.info("Aguardando comando de voz...")

            with self.microphone as source:
                # Ajustar para ruído ambiente
                logger.debug("Calibrando para ruído ambiente...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

                # Escutar
                logger.debug("Escutando...")
                phrase_time_limit = self.config.get("voice", {}).get("phrase_time_limit", 5)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            # Reconhecer usando Google Speech Recognition (gratuito)
            logger.debug("Processando audio...")
            language = self.config.get("voice", {}).get("language", "pt-BR")
            text = self.recognizer.recognize_google(audio, language=language)

            logger.info(f"Reconhecido: {text}")
            return text

        except sr.WaitTimeoutError:
            logger.debug("Timeout - nenhum audio detectado")
            return None
        except sr.UnknownValueError:
            logger.warning("Não foi possível entender o audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Erro no serviço de reconhecimento: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro ao escutar: {e}", exc_info=True)
            return None

    def listen_for_wake_word(self, wake_word: str = None) -> bool:
        """
        Escuta pela palavra de ativação

        Args:
            wake_word: Palavra de ativação (default: do config)

        Returns:
            True se detectou wake word, False caso contrário
        """
        if wake_word is None:
            wake_word = self.config.get("voice", {}).get("wake_word", "prometheus")

        text = self.listen_once()

        if text and wake_word.lower() in text.lower():
            logger.info(f"Wake word '{wake_word}' detectada!")
            return True

        return False

    def listen_continuous(self, callback, stop_event=None):
        """
        Escuta continuamente por comandos

        Args:
            callback: Função a ser chamada com o texto reconhecido
            stop_event: threading.Event para parar o loop
        """
        if not SPEECH_RECOGNITION_AVAILABLE or not self.enabled:
            logger.error("Voice listener não disponível")
            return

        logger.info("Iniciando escuta contínua...")

        while True:
            if stop_event and stop_event.is_set():
                logger.info("Parando escuta contínua")
                break

            try:
                # Escutar por wake word
                if self.listen_for_wake_word():
                    logger.info("Aguardando comando...")

                    # Escutar comando
                    command = self.listen_once(timeout=10)

                    if command:
                        callback(command)
                    else:
                        logger.info("Nenhum comando detectado")

                time.sleep(0.5)

            except KeyboardInterrupt:
                logger.info("Interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro na escuta contínua: {e}", exc_info=True)
                time.sleep(2)

    def write_to_queue(self, command: str, queue_file: str = None):
        """
        Escreve comando na fila de processamento

        Args:
            command: Comando a ser escrito
            queue_file: Arquivo de fila (default: do config)
        """
        try:
            if queue_file is None:
                queue_file = self.config.get("runtime", {}).get("queue_file", "./runtime/commands_queue.txt")

            # Criar diretório se não existir
            os.makedirs(os.path.dirname(queue_file), exist_ok=True)

            # Escrever comando
            with open(queue_file, 'a', encoding='utf-8') as f:
                f.write(f"{command}\n")

            logger.info(f"Comando adicionado à fila: {command}")

        except Exception as e:
            logger.error(f"Erro ao escrever na fila: {e}", exc_info=True)


def test_voice_recognition():
    """Função de teste para reconhecimento de voz"""
    logger.info("Iniciando teste de reconhecimento de voz")

    listener = VoiceListener()

    if not SPEECH_RECOGNITION_AVAILABLE:
        print("❌ Speech recognition não disponível")
        print("Instale com: pip install SpeechRecognition pyaudio")
        return

    print("🎤 Diga algo em 5 segundos...")
    text = listener.listen_once(timeout=5)

    if text:
        print(f"✅ Reconhecido: {text}")
    else:
        print("❌ Nada foi reconhecido")


if __name__ == "__main__":
    # Teste do módulo
    test_voice_recognition()
