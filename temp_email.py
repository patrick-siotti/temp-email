import cloudscraper
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from urllib.parse import urljoin

@dataclass
class EmailMessage:
    """Representa uma mensagem de email recebida."""
    sender: str
    subject: str
    body: str
    received_at: datetime

    @classmethod
    def from_api_response(cls, data: Dict) -> 'EmailMessage':
        """
        Cria uma instância de EmailMessage a partir da resposta da API.
        
        Args:
            data: Dicionário contendo dados da mensagem da API
            
        Returns:
            EmailMessage: Nova instância de EmailMessage
        """
        return cls(
            sender=data.get('from', ''),
            subject=data.get('subject', ''),
            body=data.get('bodyPreview', ''),
            received_at=datetime.fromisoformat(data.get('createdAt', datetime.now().isoformat()))
        )

class TempMailError(Exception):
    """Exceção base para erros relacionados ao serviço de email temporário."""
    pass

class TempMailAPIError(TempMailError):
    """Exceção para erros de API do serviço de email temporário."""
    pass

class TempMailTimeoutError(TempMailError):
    """Exceção para timeout ao aguardar novas mensagens."""
    pass

class TempMailClient:
    """Cliente para interação com serviço de email temporário."""
    
    BASE_URL = 'https://web2.temp-mail.org'
    
    def __init__(self, timeout: int = 60):
        """
        Inicializa o cliente de email temporário.
        
        Args:
            timeout (int): Tempo máximo (em segundos) para aguardar novas mensagens
        """
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.token: Optional[str] = None
        self.email: Optional[str] = None
        self.timeout = timeout
        
    def _get_url(self, endpoint: str) -> str:
        """
        Constrói a URL completa para um endpoint.
        
        Args:
            endpoint: Caminho do endpoint
            
        Returns:
            str: URL completa
        """
        return urljoin(self.BASE_URL, endpoint)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Faz uma requisição à API com tratamento de erros.
        
        Args:
            method: Método HTTP ('get' ou 'post')
            endpoint: Endpoint da API
            **kwargs: Argumentos adicionais para a requisição
            
        Returns:
            Dict: Resposta da API parseada
            
        Raises:
            TempMailAPIError: Se houver erro na requisição
        """
        try:
            if self.token:
                kwargs.setdefault('headers', {})
                kwargs['headers']['Authorization'] = f'Bearer {self.token}'
                
            request_method = getattr(self.scraper, method.lower())
            response = request_method(self._get_url(endpoint), **kwargs)
            
            if not response.ok:
                raise TempMailAPIError(f'API request failed: {response.status_code} - {response.text}')
                
            return response.json()
            
        except json.JSONDecodeError:
            raise TempMailAPIError('Invalid JSON response from API')
        except Exception as e:
            raise TempMailAPIError(f'Request failed: {str(e)}')
    
    async def generate_email(self) -> str:
        """
        Gera um novo endereço de email temporário.
        
        Returns:
            str: Endereço de email gerado
            
        Raises:
            TempMailAPIError: Se houver erro ao gerar o email
        """
        response = self._make_request('post', '/mailbox')
        
        self.token = response.get('token')
        self.email = response.get('mailbox')
        
        if not self.token or not self.email:
            raise TempMailAPIError('Failed to generate email address')
            
        return self.email
    
    async def get_messages(self) -> List[EmailMessage]:
        """
        Obtém todas as mensagens recebidas.
        
        Returns:
            List[EmailMessage]: Lista de mensagens recebidas
            
        Raises:
            TempMailAPIError: Se houver erro ao obter as mensagens
        """
        if not self.token:
            raise TempMailAPIError('No active email session')
            
        response = self._make_request('get', '/messages')
        messages = response.get('messages', [])
        
        return [EmailMessage.from_api_response(msg) for msg in messages]
    
    async def wait_for_new_message(self, check_interval: float = 1.0) -> EmailMessage:
        """
        Aguarda até que uma nova mensagem seja recebida.
        
        Args:
            check_interval: Intervalo em segundos entre verificações
            
        Returns:
            EmailMessage: Nova mensagem recebida
            
        Raises:
            TempMailTimeoutError: Se exceder o tempo limite
            TempMailAPIError: Se houver erro ao verificar mensagens
        """
        initial_messages = await self.get_messages()
        initial_count = len(initial_messages)
        
        end_time = datetime.now() + timedelta(seconds=self.timeout)
        
        while datetime.now() < end_time:
            current_messages = await self.get_messages()
            if len(current_messages) > initial_count:
                return current_messages[-1]
            await asyncio.sleep(check_interval)
            
        raise TempMailTimeoutError(f'No new messages received within {self.timeout} seconds')

async def main():
    """Exemplo de uso do cliente de email temporário."""
    client = TempMailClient(timeout=30)
    
    try:
        # Gera novo email
        email = await client.generate_email()
        print(f"Generated email: {email}")
        
        # Verifica mensagens iniciais
        messages = await client.get_messages()
        print(f"Initial messages: {len(messages)}")
        
        # Aguarda nova mensagem
        print("Waiting for new message...")
        try:
            new_message = await client.wait_for_new_message()
            print(f"New message received from: {new_message.sender}")
            print(f"Subject: {new_message.subject}")
            print(f"Body preview: {new_message.body}")
        except TempMailTimeoutError:
            print("No new messages received within timeout period")
            
    except TempMailError as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())