"""
PROMETHEUS ALWAYS-ON VOICE - Sistema de Voz Sempre Ativo com Contexto Ambiental
Implementa escuta contínua, detecção de comandos, transcrição de reuniões e contexto inteligente
"""

import os
import io
import re
import sys
import json
import time
import queue
import wave
import struct
import logging
import sqlite3
import threading
import numpy as np
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict

# Audio processing
try:
    import pyaudio
    import speech_recognition as sr
    import pyttsx3
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    # Suppress print to avoid Unicode errors on Windows
    pass

# Whisper local (opcional)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    # Suppress print to avoid Unicode errors on Windows
    pass

# Voice Activity Detection
try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    # Suppress print to avoid Unicode errors on Windows
    pass

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceMode(Enum):
    """Modos de operação de voz"""
    PASSIVE = "passive"       # Apenas escuta wake word
    ACTIVE = "active"         # Escutando comando após wake word
    CONTINUOUS = "continuous" # Transcreve tudo (reuniões)
    WHISPER = "whisper"      # Modo sussurro (sensibilidade alta)
    PRIVACY = "privacy"      # Modo privacidade (processa localmente)


class ConversationContext(Enum):
    """Tipos de contexto de conversa"""
    COMMAND = "command"           # Comando direto ao Prometheus
    MEETING = "meeting"          # Reunião sendo transcrita
    CASUAL = "casual"            # Conversa casual ambiente
    PHONE = "phone"              # Ligação telefônica
    IMPORTANT = "important"      # Conversa importante detectada


@dataclass
class AudioSegment:
    """Segmento de áudio capturado"""
    timestamp: datetime
    audio_data: bytes
    sample_rate: int
    duration: float
    energy: float
    is_speech: bool
    transcription: Optional[str] = None
    confidence: Optional[float] = None
    context: Optional[ConversationContext] = None
    speaker: Optional[str] = None


@dataclass
class TranscriptionEvent:
    """Evento de transcrição"""
    timestamp: datetime
    text: str
    speaker: str
    confidence: float
    context: ConversationContext
    keywords: List[str]
    action_items: List[str]
    sentiment: Optional[str] = None


class VoiceProfiler:
    """Perfilador de voz para identificação de falantes"""
    
    def __init__(self, profile_dir: str = "voice_profiles"):
        """
        Inicializa perfilador de voz
        
        Args:
            profile_dir: Diretório para salvar perfis de voz
        """
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(exist_ok=True)
        
        self.profiles = {}
        self.current_speaker = "unknown"
        self._load_profiles()
    
    def _load_profiles(self):
        """Carrega perfis de voz salvos"""
        for profile_file in self.profile_dir.glob("*.json"):
            with open(profile_file, 'r') as f:
                profile = json.load(f)
                self.profiles[profile['name']] = profile
        
        logger.info(f"Carregados {len(self.profiles)} perfis de voz")
    
    def identify_speaker(self, audio_features: Dict) -> str:
        """
        Identifica falante baseado em características de áudio
        
        Args:
            audio_features: Características extraídas do áudio
            
        Returns:
            Nome do falante identificado
        """
        # Implementação simplificada
        # Em produção, usar técnicas de speaker diarization
        
        if not self.profiles:
            return "user"
        
        # Por enquanto, retorna usuário principal
        return "user"
    
    def train_profile(self, name: str, audio_samples: List[bytes]):
        """
        Treina perfil de voz para um falante
        
        Args:
            name: Nome do falante
            audio_samples: Amostras de áudio para treino
        """
        # Extrai características (simplificado)
        profile = {
            'name': name,
            'created': datetime.now().isoformat(),
            'samples': len(audio_samples),
            'features': {}  # Adicionar extração de features reais
        }
        
        # Salva perfil
        profile_path = self.profile_dir / f"{name}.json"
        with open(profile_path, 'w') as f:
            json.dump(profile, f)
        
        self.profiles[name] = profile
        logger.info(f"Perfil de voz criado para: {name}")


class ContextAnalyzer:
    """Analisador de contexto de conversas"""
    
    def __init__(self):
        """Inicializa analisador de contexto"""
        self.keywords = {
            ConversationContext.MEETING: [
                'reunião', 'meeting', 'agenda', 'pauta', 'próximo item',
                'ação', 'deadline', 'prazo', 'responsável'
            ],
            ConversationContext.IMPORTANT: [
                'importante', 'urgente', 'crítico', 'prioridade',
                'deadline', 'compromisso', 'prometo', 'combinado'
            ],
            ConversationContext.PHONE: [
                'alô', 'quem fala', 'ligação', 'telefone'
            ],
            ConversationContext.COMMAND: [
                'prometheus', 'jarvis', 'assistente', 'comando'
            ]
        }
        
        self.action_patterns = [
            r'(?:preciso|precisa|deve|devemos) (.+)',
            r'(?:fazer|criar|enviar|preparar) (.+?) até (.+)',
            r'(?:vou|vai|vamos) (.+)',
            r'(?:lembrar|lembre|reminder) (?:de |que )(.+)',
            r'(?:agendar|marcar|schedule) (.+)',
            r'até (?:segunda|terça|quarta|quinta|sexta|amanhã|hoje)',
        ]
    
    def analyze_context(self, text: str) -> ConversationContext:
        """
        Analisa contexto da conversa
        
        Args:
            text: Texto transcrito
            
        Returns:
            Tipo de contexto detectado
        """
        text_lower = text.lower()
        
        # Conta palavras-chave para cada contexto
        context_scores = {}
        
        for context, keywords in self.keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                context_scores[context] = score
        
        # Retorna contexto com maior score
        if context_scores:
            return max(context_scores, key=context_scores.get)
        
        return ConversationContext.CASUAL
    
    def extract_action_items(self, text: str) -> List[str]:
        """
        Extrai itens de ação do texto
        
        Args:
            text: Texto transcrito
            
        Returns:
            Lista de ações detectadas
        """
        actions = []
        
        for pattern in self.action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    action = ' '.join(match).strip()
                else:
                    action = match.strip()
                
                if len(action) > 5:  # Filtra ações muito curtas
                    actions.append(action)
        
        return actions
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extrai palavras-chave importantes
        
        Args:
            text: Texto transcrito
            
        Returns:
            Lista de keywords
        """
        keywords = []
        
        # Padrões de palavras importantes
        important_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Datas
            r'\b\d{1,2}:\d{2}\b',                    # Horários
            r'\b[A-Z][A-Z]+\b',                      # Siglas
            r'\b\d+(?:\.\d+)?%\b',                   # Porcentagens
            r'R\$\s*\d+(?:\.\d+)?',                  # Valores monetários
            r'\b(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\b',
            r'\b(?:segunda|terça|quarta|quinta|sexta|sábado|domingo)\b',
        ]
        
        for pattern in important_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        # Remove duplicatas e retorna
        return list(set(keywords))
    
    def detect_sentiment(self, text: str) -> str:
        """
        Detecta sentimento básico do texto
        
        Args:
            text: Texto transcrito
            
        Returns:
            Sentimento detectado (positivo/negativo/neutro)
        """
        positive_words = [
            'bom', 'ótimo', 'excelente', 'perfeito', 'maravilhoso',
            'sucesso', 'parabéns', 'feliz', 'satisfeito', 'aprovado'
        ]
        
        negative_words = [
            'ruim', 'péssimo', 'terrível', 'problema', 'erro',
            'falha', 'atraso', 'cancelado', 'negado', 'preocupado'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"


class AlwaysOnVoiceSystem:
    """Sistema principal de voz sempre ativo"""
    
    def __init__(self, wake_words: List[str] = None,
                 whisper_model: str = "base",
                 save_transcriptions: bool = True):
        """
        Inicializa sistema de voz sempre ativo
        
        Args:
            wake_words: Palavras de ativação
            whisper_model: Modelo Whisper para usar (se disponível)
            save_transcriptions: Se deve salvar transcrições
        """
        if not AUDIO_AVAILABLE:
            raise Exception("Bibliotecas de áudio não disponíveis")
        
        # Wake words
        self.wake_words = wake_words or ["prometheus", "jarvis", "assistente"]
        
        # Modo atual
        self.mode = VoiceMode.PASSIVE
        self.is_listening = False
        
        # Reconhecedor de voz
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Calibra para ruído ambiente
        with self.microphone as source:
            logger.info("Calibrando para ruído ambiente...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        
        # TTS para feedback
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 180)
        self.tts_engine.setProperty('voice', self.tts_engine.getProperty('voices')[0].id)
        
        # Whisper local se disponível
        self.whisper_model = None
        if WHISPER_AVAILABLE:
            try:
                logger.info(f"Carregando modelo Whisper {whisper_model}...")
                self.whisper_model = whisper.load_model(whisper_model)
                logger.info("Whisper carregado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao carregar Whisper: {e}")
        
        # VAD se disponível
        self.vad = None
        if VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(2)  # Agressividade 0-3
        
        # Profiler e analyzer
        self.profiler = VoiceProfiler()
        self.context_analyzer = ContextAnalyzer()
        
        # Buffers
        self.audio_buffer = deque(maxlen=100)  # Últimos 100 segmentos
        self.transcription_buffer = deque(maxlen=50)  # Últimas 50 transcrições
        self.command_queue = queue.Queue()
        
        # Database para transcrições
        if save_transcriptions:
            self.db_path = "prometheus_transcriptions.db"
            self._init_database()
        else:
            self.db_path = None
        
        # Threads
        self.listen_thread = None
        self.process_thread = None
        
        # Callbacks
        self.callbacks = {
            'on_wake_word': None,
            'on_command': None,
            'on_transcription': None,
            'on_action_item': None,
            'on_important': None
        }
        
        # Estatísticas
        self.stats = {
            'total_transcriptions': 0,
            'commands_processed': 0,
            'action_items_detected': 0,
            'meetings_transcribed': 0,
            'wake_word_detections': 0
        }
    
    def _init_database(self):
        """Inicializa banco de dados para transcrições"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                text TEXT,
                speaker TEXT,
                context TEXT,
                confidence REAL,
                keywords TEXT,
                action_items TEXT,
                sentiment TEXT,
                audio_file TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def start(self):
        """Inicia o sistema de escuta"""
        if self.is_listening:
            logger.warning("Sistema já está escutando")
            return
        
        self.is_listening = True
        
        # Inicia thread de escuta
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        # Inicia thread de processamento
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        logger.info("🎤 Sistema Always-On iniciado")
        self.speak("Sistema de voz ativado. Diga 'Prometheus' para comandos.")
    
    def stop(self):
        """Para o sistema de escuta"""
        self.is_listening = False
        
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        
        if self.process_thread:
            self.process_thread.join(timeout=2)
        
        logger.info("Sistema de voz parado")
    
    def _listen_loop(self):
        """Loop principal de escuta"""
        logger.info("Iniciando loop de escuta...")
        
        with self.microphone as source:
            while self.is_listening:
                try:
                    # Escuta por áudio
                    audio = self.recognizer.listen(
                        source, 
                        timeout=1,
                        phrase_time_limit=5
                    )
                    
                    # Cria segmento
                    segment = AudioSegment(
                        timestamp=datetime.now(),
                        audio_data=audio.get_wav_data(),
                        sample_rate=audio.sample_rate,
                        duration=len(audio.frame_data) / audio.sample_rate,
                        energy=self._calculate_energy(audio.frame_data),
                        is_speech=True
                    )
                    
                    # Adiciona ao buffer
                    self.audio_buffer.append(segment)
                    
                    # Processa baseado no modo
                    if self.mode == VoiceMode.PASSIVE:
                        self._process_passive(segment)
                    elif self.mode == VoiceMode.ACTIVE:
                        self._process_active(segment)
                    elif self.mode == VoiceMode.CONTINUOUS:
                        self._process_continuous(segment)
                    elif self.mode == VoiceMode.WHISPER:
                        self._process_whisper(segment)
                    
                except sr.WaitTimeoutError:
                    # Timeout normal, continua escutando
                    pass
                except Exception as e:
                    logger.error(f"Erro no loop de escuta: {e}")
    
    def _process_passive(self, segment: AudioSegment):
        """Processa áudio em modo passivo (apenas wake word)"""
        try:
            # Transcreve com Google Speech API (rápido)
            text = self.recognizer.recognize_google(
                sr.AudioData(segment.audio_data, segment.sample_rate, 2),
                language="pt-BR"
            ).lower()
            
            segment.transcription = text
            
            # Verifica wake word
            for wake_word in self.wake_words:
                if wake_word.lower() in text:
                    logger.info(f"🎯 Wake word detectado: {wake_word}")
                    self.stats['wake_word_detections'] += 1
                    
                    # Muda para modo ativo
                    self.mode = VoiceMode.ACTIVE
                    self.speak("Sim?")
                    
                    # Callback
                    if self.callbacks['on_wake_word']:
                        self.callbacks['on_wake_word'](wake_word)
                    
                    # Timer para voltar ao modo passivo
                    threading.Timer(10.0, self._return_to_passive).start()
                    
                    break
            
            # Verifica se tem algo importante mesmo sem wake word
            if any(word in text for word in ['urgente', 'importante', 'emergência']):
                self._process_important_detection(text)
                
        except sr.UnknownValueError:
            # Não conseguiu entender, ignora
            pass
        except Exception as e:
            logger.error(f"Erro ao processar modo passivo: {e}")
    
    def _process_active(self, segment: AudioSegment):
        """Processa áudio em modo ativo (após wake word)"""
        try:
            # Usa Whisper se disponível (melhor qualidade)
            if self.whisper_model:
                text = self._transcribe_with_whisper(segment.audio_data)
            else:
                text = self.recognizer.recognize_google(
                    sr.AudioData(segment.audio_data, segment.sample_rate, 2),
                    language="pt-BR"
                )
            
            segment.transcription = text
            self.stats['commands_processed'] += 1
            
            logger.info(f"📝 Comando: {text}")
            
            # Adiciona comando à fila
            self.command_queue.put({
                'text': text,
                'timestamp': segment.timestamp,
                'confidence': segment.confidence or 0.9
            })
            
            # Callback
            if self.callbacks['on_command']:
                self.callbacks['on_command'](text)
            
            # Feedback
            self.speak("Entendido")
            
            # Volta ao modo passivo
            self.mode = VoiceMode.PASSIVE
            
        except sr.UnknownValueError:
            self.speak("Não entendi, pode repetir?")
        except Exception as e:
            logger.error(f"Erro ao processar comando: {e}")
    
    def _process_continuous(self, segment: AudioSegment):
        """Processa áudio em modo contínuo (transcreve tudo)"""
        try:
            # Sempre usa melhor engine disponível
            if self.whisper_model:
                text = self._transcribe_with_whisper(segment.audio_data)
                confidence = 0.95
            else:
                text = self.recognizer.recognize_google(
                    sr.AudioData(segment.audio_data, segment.sample_rate, 2),
                    language="pt-BR",
                    show_all=True
                )
                
                if text and 'alternative' in text:
                    text = text['alternative'][0]['transcript']
                    confidence = text['alternative'][0].get('confidence', 0.8)
                else:
                    return
            
            segment.transcription = text
            segment.confidence = confidence
            
            # Analisa contexto
            context = self.context_analyzer.analyze_context(text)
            segment.context = context
            
            # Identifica falante
            speaker = self.profiler.identify_speaker({'audio': segment.audio_data})
            segment.speaker = speaker
            
            # Extrai informações
            keywords = self.context_analyzer.extract_keywords(text)
            action_items = self.context_analyzer.extract_action_items(text)
            sentiment = self.context_analyzer.detect_sentiment(text)
            
            # Cria evento de transcrição
            event = TranscriptionEvent(
                timestamp=segment.timestamp,
                text=text,
                speaker=speaker,
                confidence=confidence,
                context=context,
                keywords=keywords,
                action_items=action_items,
                sentiment=sentiment
            )
            
            # Adiciona ao buffer
            self.transcription_buffer.append(event)
            self.stats['total_transcriptions'] += 1
            
            # Salva no banco se configurado
            if self.db_path:
                self._save_transcription(event)
            
            # Callbacks
            if self.callbacks['on_transcription']:
                self.callbacks['on_transcription'](event)
            
            if action_items and self.callbacks['on_action_item']:
                for action in action_items:
                    self.callbacks['on_action_item'](action, speaker)
                    self.stats['action_items_detected'] += 1
            
            # Log
            logger.info(f"[{speaker}] {text[:100]}...")
            if action_items:
                logger.info(f"  📌 Ações: {action_items}")
            
        except Exception as e:
            logger.error(f"Erro ao processar modo contínuo: {e}")
    
    def _process_whisper(self, segment: AudioSegment):
        """Processa áudio em modo sussurro (alta sensibilidade)"""
        # Similar ao modo ativo mas com sensibilidade maior
        self.recognizer.energy_threshold = 100  # Reduz threshold
        self._process_active(segment)
        self.recognizer.energy_threshold = 300  # Volta ao normal
    
    def _process_important_detection(self, text: str):
        """Processa detecção de conversa importante"""
        logger.warning(f"⚠️ Conversa importante detectada: {text}")
        
        # Inicia transcrição automática temporária
        self.mode = VoiceMode.CONTINUOUS
        
        # Callback
        if self.callbacks['on_important']:
            self.callbacks['on_important'](text)
        
        # Volta ao normal após 5 minutos
        threading.Timer(300.0, self._return_to_passive).start()
    
    def _return_to_passive(self):
        """Retorna ao modo passivo"""
        if self.mode != VoiceMode.CONTINUOUS:
            self.mode = VoiceMode.PASSIVE
            logger.info("Retornado ao modo passivo")
    
    def _transcribe_with_whisper(self, audio_data: bytes) -> str:
        """Transcreve usando Whisper local"""
        if not self.whisper_model:
            raise Exception("Whisper não disponível")
        
        # Salva temporariamente
        temp_file = f"temp_{datetime.now().timestamp()}.wav"
        
        with wave.open(temp_file, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data)
        
        try:
            # Transcreve
            result = self.whisper_model.transcribe(
                temp_file,
                language='pt',
                task='transcribe'
            )
            
            return result['text'].strip()
            
        finally:
            # Remove arquivo temporário
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _calculate_energy(self, audio_data) -> float:
        """Calcula energia do áudio"""
        if isinstance(audio_data, bytes):
            # Converte bytes para array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
        else:
            audio_array = np.array(audio_data)
        
        # RMS energy
        return np.sqrt(np.mean(audio_array**2))
    
    def _save_transcription(self, event: TranscriptionEvent):
        """Salva transcrição no banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO transcriptions 
            (timestamp, text, speaker, context, confidence, 
             keywords, action_items, sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.timestamp.timestamp(),
            event.text,
            event.speaker,
            event.context.value,
            event.confidence,
            json.dumps(event.keywords),
            json.dumps(event.action_items),
            event.sentiment
        ))
        
        conn.commit()
        conn.close()
    
    def _process_loop(self):
        """Loop de processamento de comandos"""
        while self.is_listening:
            try:
                # Processa comandos da fila
                if not self.command_queue.empty():
                    command = self.command_queue.get(timeout=0.1)
                    # Aqui integraria com o Prometheus principal
                    logger.info(f"Processando comando: {command['text']}")
                
                time.sleep(0.1)
                
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Erro no loop de processamento: {e}")
    
    def speak(self, text: str, wait: bool = False):
        """
        Fala texto usando TTS
        
        Args:
            text: Texto para falar
            wait: Se deve esperar terminar de falar
        """
        if wait:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        else:
            # Fala em thread separada
            def speak_async():
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            
            threading.Thread(target=speak_async, daemon=True).start()
    
    def set_mode(self, mode: VoiceMode):
        """
        Define modo de operação
        
        Args:
            mode: Novo modo
        """
        old_mode = self.mode
        self.mode = mode
        
        logger.info(f"Modo alterado: {old_mode.value} -> {mode.value}")
        
        if mode == VoiceMode.CONTINUOUS:
            self.speak("Modo de transcrição contínua ativado")
            self.stats['meetings_transcribed'] += 1
        elif mode == VoiceMode.WHISPER:
            self.speak("Modo sussurro ativado", wait=True)
        elif mode == VoiceMode.PRIVACY:
            self.speak("Modo privacidade ativado. Processamento local apenas.")
    
    def register_callback(self, event: str, callback: Callable):
        """
        Registra callback para evento
        
        Args:
            event: Nome do evento
            callback: Função callback
        """
        if event in self.callbacks:
            self.callbacks[event] = callback
            logger.info(f"Callback registrado para: {event}")
    
    def get_recent_transcriptions(self, limit: int = 10) -> List[TranscriptionEvent]:
        """
        Retorna transcrições recentes
        
        Args:
            limit: Número máximo de transcrições
            
        Returns:
            Lista de eventos de transcrição
        """
        return list(self.transcription_buffer)[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        return {
            **self.stats,
            'current_mode': self.mode.value,
            'is_listening': self.is_listening,
            'buffer_size': len(self.audio_buffer),
            'transcriptions_in_buffer': len(self.transcription_buffer),
            'registered_callbacks': sum(1 for cb in self.callbacks.values() if cb),
            'voice_profiles': len(self.profiler.profiles)
        }
    
    def export_meeting_transcript(self, start_time: datetime, 
                                  end_time: datetime) -> str:
        """
        Exporta transcrição de reunião
        
        Args:
            start_time: Início da reunião
            end_time: Fim da reunião
            
        Returns:
            Transcrição formatada
        """
        if not self.db_path:
            return "Sistema não está salvando transcrições"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, speaker, text, action_items
            FROM transcriptions
            WHERE timestamp BETWEEN ? AND ?
            AND context IN ('meeting', 'important')
            ORDER BY timestamp
        """, (start_time.timestamp(), end_time.timestamp()))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Formata transcrição
        transcript = f"# Transcrição de Reunião\n"
        transcript += f"**Data:** {start_time.strftime('%d/%m/%Y')}\n"
        transcript += f"**Horário:** {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}\n\n"
        
        transcript += "## Conversa\n\n"
        
        for row in rows:
            timestamp = datetime.fromtimestamp(row[0])
            speaker = row[1]
            text = row[2]
            
            transcript += f"**[{timestamp.strftime('%H:%M:%S')}] {speaker}:** {text}\n\n"
        
        # Adiciona resumo de ações
        transcript += "\n## Itens de Ação\n\n"
        
        action_items = []
        for row in rows:
            if row[3]:  # action_items
                items = json.loads(row[3])
                action_items.extend(items)
        
        if action_items:
            for i, action in enumerate(set(action_items), 1):
                transcript += f"{i}. {action}\n"
        else:
            transcript += "Nenhum item de ação identificado.\n"
        
        return transcript


class PrometheusVoiceInterface:
    """Interface simplificada para integração com Prometheus"""
    
    def __init__(self, wake_words: List[str] = None):
        """
        Inicializa interface de voz
        
        Args:
            wake_words: Palavras de ativação personalizadas
        """
        self.voice_system = AlwaysOnVoiceSystem(wake_words=wake_words)
        
        # Registra callbacks
        self.voice_system.register_callback('on_command', self._handle_command)
        self.voice_system.register_callback('on_action_item', self._handle_action)
        self.voice_system.register_callback('on_important', self._handle_important)
        
        self.command_handler = None
        
        logger.info("Interface de voz Prometheus inicializada")
    
    def start(self):
        """Inicia sistema de voz"""
        self.voice_system.start()
        return {"status": "started", "mode": "passive"}
    
    def stop(self):
        """Para sistema de voz"""
        self.voice_system.stop()
        return {"status": "stopped"}
    
    def _handle_command(self, text: str):
        """Processa comando de voz"""
        logger.info(f"Comando recebido: {text}")
        
        if self.command_handler:
            result = self.command_handler(text)
            
            # Fala resultado
            if isinstance(result, dict) and 'message' in result:
                self.voice_system.speak(result['message'])
    
    def _handle_action(self, action: str, speaker: str):
        """Processa item de ação detectado"""
        logger.info(f"📌 Ação detectada de {speaker}: {action}")
        
        # Aqui poderia criar tarefa, lembrete, etc
        # Por exemplo, integrar com sistema de tarefas
    
    def _handle_important(self, text: str):
        """Processa detecção de conversa importante"""
        logger.warning(f"⚠️ Importante: {text}")
        
        # Poderia enviar notificação, email, etc
    
    def set_command_handler(self, handler: Callable):
        """Define handler para comandos"""
        self.command_handler = handler
    
    def transcribe_meeting(self, duration_minutes: int = 60):
        """
        Inicia transcrição de reunião
        
        Args:
            duration_minutes: Duração da reunião em minutos
        """
        self.voice_system.set_mode(VoiceMode.CONTINUOUS)
        
        # Agenda volta ao modo normal
        def stop_meeting():
            self.voice_system.set_mode(VoiceMode.PASSIVE)
            logger.info("Transcrição de reunião finalizada")
        
        threading.Timer(duration_minutes * 60, stop_meeting).start()
        
        return {
            "status": "meeting_mode",
            "duration": duration_minutes,
            "message": f"Transcrevendo reunião por {duration_minutes} minutos"
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do sistema"""
        return {
            "active": self.voice_system.is_listening,
            "mode": self.voice_system.mode.value,
            "stats": self.voice_system.get_statistics(),
            "recent_transcriptions": len(self.voice_system.transcription_buffer)
        }


if __name__ == "__main__":
    print("🎤 Testando Sistema Always-On Voice...")
    
    if not AUDIO_AVAILABLE:
        print("❌ Bibliotecas de áudio não disponíveis")
        print("Instale com: pip install pyaudio SpeechRecognition pyttsx3")
        sys.exit(1)
    
    # Inicializa interface
    voice_interface = PrometheusVoiceInterface(
        wake_words=["prometheus", "jarvis", "computador"]
    )
    
    # Define handler de teste
    def test_handler(command):
        print(f"  Comando processado: {command}")
        return {"message": "Comando recebido"}
    
    voice_interface.set_command_handler(test_handler)
    
    print("\n📊 Iniciando sistema...")
    result = voice_interface.start()
    print(f"  Status: {result}")
    
    print("\n🎙️ Modos disponíveis:")
    print("  - Diga 'Prometheus' para ativar comandos")
    print("  - Sistema detecta conversas importantes automaticamente")
    print("  - Transcreve reuniões quando ativado")
    
    print("\n⏸️ Comandos de controle:")
    print("  - Digite 'meeting' para modo reunião")
    print("  - Digite 'status' para ver estatísticas")
    print("  - Digite 'quit' para sair")
    
    try:
        while True:
            cmd = input("\n> ").lower()
            
            if cmd == 'quit':
                break
            elif cmd == 'meeting':
                result = voice_interface.transcribe_meeting(duration_minutes=5)
                print(f"  {result['message']}")
            elif cmd == 'status':
                status = voice_interface.get_status()
                print(f"  Modo: {status['mode']}")
                print(f"  Stats: {status['stats']}")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Interrompido pelo usuário")
    
    finally:
        voice_interface.stop()
        print("\n✅ Sistema Always-On Voice finalizado!")
