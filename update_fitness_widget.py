#!/usr/bin/env python3
"""
Google Health API - Fitness Widget Updater
Obtiene datos de fitness desde Google Health API y genera un SVG widget
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

# Metas semanales (para calcular progreso)
WEEKLY_GOALS = {
    'steps': 70000,      # ~10,000 pasos/día
    'calories': 14000,   # ~2,000 cal/día
    'active_minutes': 210  # ~30 min/día
}

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
        
        return {
            'steps': total_steps,
            'calories': int(total_calories),
            'active_minutes': total_active_minutes
        }
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"   Respuesta: {e.response.text}")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

def format_number(num):
    """Formatea números con comas para miles"""
    return f"{num:,}"

def calculate_progress(value, goal, max_width=200):
    """Calcula el ancho de la barra de progreso"""
    if goal == 0:
        return 0
    progress = min((value / goal) * 100, 100)
    return int((progress / 100) * max_width)

def generate_svg_widget(stats, week_range, days_elapsed):
    """Genera el SVG widget con las estadísticas"""
    template_path = '../profile-repo/assets/fitness-widget.svg'
    output_path = '../profile-repo/assets/fitness-widget.svg'
    
    if not os.path.exists(template_path):
        print(f"⚠️  No se encontró template en {template_path}")
        return
    
    with open(template_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    # Calcular promedios diarios
    steps_avg = stats['steps'] // days_elapsed if days_elapsed > 0 else 0
    calories_avg = stats['calories'] // days_elapsed if days_elapsed > 0 else 0
    active_avg = stats['active_minutes'] // days_elapsed if days_elapsed > 0 else 0
    
    # Calcular barras de progreso
    steps_progress = calculate_progress(stats['steps'], WEEKLY_GOALS['steps'])
    calories_progress = calculate_progress(stats['calories'], WEEKLY_GOALS['calories'])
    active_progress = calculate_progress(stats['active_minutes'], WEEKLY_GOALS['active_minutes'])
    
    # Reemplazar placeholders
    replacements = {
        '{{DATE_RANGE}}': week_range,
        '{{STEPS}}': format_number(stats['steps']),
        '{{CALORIES}}': format_number(stats['calories']),
        '{{ACTIVE_MINUTES}}': format_number(stats['active_minutes']),
        '{{STEPS_AVG}}': format_number(steps_avg),
        '{{CALORIES_AVG}}': format_number(calories_avg),
        '{{ACTIVE_AVG}}': format_number(active_avg),
        '{{STEPS_PROGRESS}}': str(steps_progress),
        '{{CALORIES_PROGRESS}}': str(calories_progress),
        '{{ACTIVE_PROGRESS}}': str(active_progress),
        '{{LAST_UPDATED}}': datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    }
    
    for placeholder, value in replacements.items():
        svg_content = svg_content.replace(placeholder, value)
    
    # Guardar SVG actualizado
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"✅ SVG widget generado en {output_path}")

def update_readme():
    """Actualiza el README para usar el SVG widget"""
    readme_path = '../profile-repo/README.md'
    
    if not os.path.exists(readme_path):
        print(f"⚠️  No se encontró {readme_path}")
        return
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crear referencia al SVG
    widget_section = """### 🏃 Fitness Stats

<img src="./assets/fitness-widget.svg" alt="Fitness Stats" width="100%" />"""
    
    # Buscar y reemplazar sección de fitness
    import re
    pattern = r'### 🏃 Fitness Stats.*?(?=\n###|\n---|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, widget_section, content, flags=re.DOTALL)
    else:
        # Si no existe, agregar antes del último ---
        parts = content.rsplit('\n---\n', 1)
        if len(parts) == 2:
            new_content = parts[0] + '\n\n' + widget_section + '\n\n---\n' + parts[1]
        else:
            new_content = content + '\n\n' + widget_section
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ README actualizado para usar SVG widget")

def main():
    """Función principal"""
    print("🚀 Google Health API - Fitness Widget Updater\n")
    
    # Cargar credenciales
    creds = load_credentials()
    
    # Calcular rango de fechas (mes actual: desde el 1 hasta hoy)
    today = datetime.now()
    start_of_month = today.replace(day=1)
    days_elapsed = today.day
    
    # Obtener datos
    stats = get_fitness_data(creds, start_of_month, today)
    
    # Mostrar resultados
    print("\n📈 Estadísticas obtenidas (totales del mes):")
    print(f"  👟 Pasos: {stats['steps']:,}")
    print(f"  🔥 Calorías: {stats['calories']:,}")
    print(f"  ⏱️  Minutos activos: {stats['active_minutes']:,}")
    
    # Generar SVG widget
    month_range = f"{start_of_month.strftime('%B %Y')}"
    generate_svg_widget(stats, month_range, days_elapsed)
    
    # Actualizar README
    update_readme()
    
    print("\n✅ Proceso completado exitosamente!")

if __name__ == '__main__':
    main()