# logger_config.py
import logging
import sys

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout) # Envia logs para a saída padrão
        ]
    )
    # Retorna um logger nomeado para o compilador principal, se desejado,
    # ou apenas configura o logger raiz.
    return logging.getLogger("miniportugolCompilador")

# Configura o logger quando este módulo é importado pela primeira vez.
# As classes individuais podem obter seus próprios loggers com logging.getLogger(__name__)
# ou logging.getLogger(self.__class__.__name__)
setup_logger()
