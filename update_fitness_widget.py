#!/usr/bin/env python3
"""
Google Health API - Fitness Widget Updater
Obtiene datos de fitness desde Google Health API y actualiza el README
"""

import os
import json
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Configuración
SCOPES = ['https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly']
API_BASE = 'https://health.googleapis.com/v4'

def load_credentials():
    """Carga y valida las credenciales OAuth2"""
    if not os.path.exists('token.json'):
        raise FileNotFoundError("❌ No se encontró token.json. Ejecuta primero: python google_health_setup.py")
    
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Renovar token si expiró
    if creds.expired and creds.refresh_token:
        print("🔄 Renovando access token...")
        creds.refresh(Request())
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_fitness_data(creds, start_date, end_date):
    """Obtiene datos de fitness desde Google Health API"""
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }
    
    # Formato de fecha para el filtro (Google Health API solo soporta >= y <, no <=)
    start_str = start_date.strftime('%Y-%m-%dT00:00:00')
    # Agregar 1 día para usar < en lugar de <=
    end_date_plus_one = end_date + timedelta(days=1)
    end_str = end_date_plus_one.strftime('%Y-%m-%dT00:00:00')
    
    print(f"📊 Consultando datos del {start_date.date()} al {end_date.date()}...")
    
    # 1. Obtener datos de ejercicio
    exercise_url = f'{API_BASE}/users/me/dataTypes/exercise/dataPoints'
    exercise_params = {
        'filter': f'exercise.interval.civil_start_time >= "{start_str}" AND exercise.interval.civil_start_time < "{end_str}"'
    }
    
    try:
        response = requests.get(exercise_url, headers=headers, params=exercise_params)
        response.raise_for_status()
        data = response.json()
        
        # Procesar datos de ejercicio
        total_steps = 0
        total_calories = 0
        total_active_minutes = 0
        
        data_points = data.get('dataPoints', [])
        print(f"  • Puntos de datos de ejercicio: {len(data_points)}")
        
        for point in data_points:
            exercise = point.get('exercise', {})
            metrics = exercise.get('metricsSummary', {})
            
            # Sumar métricas
            steps = metrics.get('steps', '0')
            total_steps += int(steps) if steps else 0
            total_calories += metrics.get('caloriesKcal', 0)
            
            # Calcular minutos activos desde activeDuration (formato: "900s" o "3023.500s")
            duration = exercise.get('activeDuration', '0s')
            if duration.endswith('s'):
                seconds = float(duration[:-1])
                total_active_minutes += int(seconds) // 60
        
        # 2. Obtener datos de frecuencia cardíaca
        hr_url = f'{API_BASE}/users/me/dataTypes/heart_rate/dataPoints'
        hr_params = {
            'filter': f'heart_rate.interval.civil_start_time >= "{start_str}" AND heart_rate.interval.civil_start_time < "{end_str}"'
        }
        
        min_hr = None
        max_hr = None
        
        try:
            hr_response = requests.get(hr_url, headers=headers, params=hr_params)
            hr_response.raise_for_status()
            hr_data = hr_response.json()
            
            hr_points = hr_data.get('dataPoints', [])
            print(f"  • Puntos de datos de frecuencia cardíaca: {len(hr_points)}")
            
            for point in hr_points:
                hr = point.get('heart_rate', {})
                bpm = hr.get('beatsPerMinute')
                
                if bpm:
                    if min_hr is None or bpm < min_hr:
                        min_hr = bpm
                    if max_hr is None or bpm > max_hr:
                        max_hr = bpm
        
        except requests.exceptions.HTTPError as e:
            print(f"  ⚠️  No se pudieron obtener datos de frecuencia cardíaca: {e}")
        
        return {
            'steps': total_steps,
            'calories': int(total_calories),
            'active_minutes': total_active_minutes,
            'min_heart_rate': min_hr,
            'max_heart_rate': max_hr
        }
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"   Respuesta: {e.response.text}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

def update_readme(stats, month_name):
    """Actualiza el README con las estadísticas de fitness"""
    readme_path = '../profile-repo/README.md'
    
    if not os.path.exists(readme_path):
        print(f"⚠️  No se encontró {readme_path}")
        return
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Formatear frecuencia cardíaca
    hr_text = "N/A"
    if stats['min_heart_rate'] and stats['max_heart_rate']:
        hr_text = f"{stats['min_heart_rate']} - {stats['max_heart_rate']} bpm"
    
    # Crear widget actualizado (totales del mes)
    widget = f"""## 🏃 Fitness Stats - {month_name} (Totales)

| Metric | Value |
|--------|-------|
| 👟 Steps | {stats['steps']:,} |
| 🔥 Calories | {stats['calories']:,} |
| ⏱️ Active Minutes | {stats['active_minutes']:,} |
| ❤️ Heart Rate | {hr_text} |

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*  
*Data source: Google Health API (Fitbit)*"""
    
    # Buscar y reemplazar sección de fitness
    import re
    pattern = r'## 🏃 Fitness Stats.*?(?=\n##|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, widget, content, flags=re.DOTALL)
    else:
        # Si no existe, agregar al final
        new_content = content + '\n\n' + widget
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ README actualizado en {readme_path}")

def main():
    """Función principal"""
    print("🚀 Google Health API - Fitness Widget Updater\n")
    
    # Cargar credenciales
    creds = load_credentials()
    
    # Calcular rango de fechas (mes actual)
    today = datetime.now()
    start_of_month = today.replace(day=1)
    
    # Obtener datos
    stats = get_fitness_data(creds, start_of_month, today)
    
    # Mostrar resultados
    print("\n📈 Estadísticas obtenidas (totales del mes):")
    print(f"  👟 Pasos: {stats['steps']:,}")
    print(f"  🔥 Calorías: {stats['calories']:,}")
    print(f"  ⏱️  Minutos activos: {stats['active_minutes']:,}")
    if stats['min_heart_rate'] and stats['max_heart_rate']:
        print(f"  ❤️  Frecuencia cardíaca: {stats['min_heart_rate']}-{stats['max_heart_rate']} bpm")
    else:
        print(f"  ❤️  Frecuencia cardíaca: N/A")
    
    # Actualizar README
    month_name = today.strftime('%B %Y')
    update_readme(stats, month_name)
    
    print("\n✅ Proceso completado exitosamente!")

if __name__ == '__main__':
    main()
