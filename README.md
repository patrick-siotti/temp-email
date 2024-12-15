# temp-email
Sistema de email completo descomplicado para qualquer um que quiser fazer automações que precise de email, mas não querem as apis aleatórias na net.

O script usa um sistema avançado para passar a cloudflare e consegue usar de graça a api de email temporario do temp-email de forma rapida e eficiente.

Você consegue criar sessões diferentes para cada objeto criado, podendo resetar, esperar um mensagem e verificar todo o corpo da mensagem

# exemplo de uso
```python
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
```
