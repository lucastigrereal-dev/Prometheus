# Prometheus Plugins

Sistema de plugins para estender funcionalidades do Prometheus.

## Como Criar um Plugin

Cada plugin deve ser um arquivo Python na pasta `plugins/` seguindo esta estrutura:

```python
# plugins/meu_plugin.py

class MeuPlugin:
    """
    Descrição do plugin
    """

    def __init__(self):
        self.name = "MeuPlugin"
        self.version = "1.0.0"
        self.author = "Seu Nome"

    def initialize(self, prometheus_core):
        """
        Chamado quando o plugin é carregado
        """
        self.core = prometheus_core
        print(f"{self.name} inicializado!")

    def handle_command(self, command: str) -> dict:
        """
        Processa comando

        Args:
            command: Comando em linguagem natural

        Returns:
            dict: {"success": bool, "result": any, "error": str}
        """
        # Seu código aqui
        return {"success": True, "result": "OK"}

    def shutdown(self):
        """
        Chamado quando o Prometheus é desligado
        """
        print(f"{self.name} desligado!")
```

## Plugins Disponíveis

(Ainda nenhum - você pode criar o primeiro!)

## Ideias de Plugins

- **Spotify Control**: Controlar música via Spotify API
- **Email Monitor**: Monitorar emails e notificar
- **Task Scheduler**: Agendar tarefas recorrentes
- **Weather**: Informações meteorológicas
- **News**: Agregador de notícias
- **Translation**: Tradução automática
- **OCR Advanced**: OCR com múltiplos engines
- **Speech Synthesis**: TTS com vozes customizadas

## Instalação de Plugin

1. Coloque o arquivo `.py` na pasta `plugins/`
2. Reinicie o Prometheus
3. O plugin será carregado automaticamente

## Desabilitar Plugin

Renomeie o arquivo para `.py.disabled`:

```bash
mv plugins/meu_plugin.py plugins/meu_plugin.py.disabled
```
