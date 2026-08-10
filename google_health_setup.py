#!/usr/bin/env python3
"""
Google Health API OAuth2 Setup Script
Configura la autenticación OAuth2 para acceder a Google Health API (Fitbit data)
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes necesarios para Google Health API
SCOPES = ['https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly']

def main():
    """Ejecuta el flujo OAuth2 y guarda las credenciales"""
    creds = None
    
    # Verificar si ya existe token.json
    if os.path.exists('token.json'):
        print("⚠️  Ya existe un archivo token.json")
        response = input("¿Deseas sobrescribirlo? (s/n): ")
        if response.lower() != 's':
            print("❌ Operación cancelada")
            return
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Si no hay credenciales válidas, iniciar flujo OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token expirado...")
            creds.refresh(Request())
        else:
            # Verificar que exista credentials.json
            if not os.path.exists('credentials.json'):
                print("❌ Error: No se encontró credentials.json")
                print("\n📋 Pasos para obtener credentials.json:")
                print("1. Ve a: https://console.cloud.google.com/")
                print("2. Crea un proyecto nuevo o selecciona uno existente")
                print("3. Habilita 'Google Health API'")
                print("4. Ve a 'Credenciales' → 'Crear credenciales' → 'ID de cliente de OAuth 2.0'")
                print("5. Tipo de aplicación: 'Aplicación de escritorio'")
                print("6. Descarga el JSON y guárdalo como 'credentials.json'")
                print("7. Agrega tu email en 'Pantalla de consentimiento de OAuth' → 'Usuarios de prueba'")
                return
            
            print("🔐 Iniciando flujo de autenticación OAuth2...")
            print("Se abrirá tu navegador para autorizar el acceso")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', 
                SCOPES,
                redirect_uri='http://localhost:8080/'
            )
            creds = flow.run_local_server(port=8080)
        
        # Guardar credenciales
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("✅ Token guardado exitosamente en token.json")
    
    # Mostrar información del token
    token_data = json.loads(creds.to_json())
    print("\n📊 Información del token:")
    print(f"  • Token válido: {'✅' if creds.valid else '❌'}")
    print(f"  • Tiene refresh_token: {'✅' if creds.refresh_token else '❌'}")
    if creds.expiry:
        print(f"  • Expira: {creds.expiry}")
    
    print("\n🎉 Configuración completada!")
    print("\n📝 Próximos pasos:")
    print("1. Guarda el contenido de token.json como secret en GitHub:")
    print("   Nombre: GOOGLE_HEALTH_TOKEN")
    print("2. Ejecuta: python update_fitness_widget.py")

if __name__ == '__main__':
    main()
