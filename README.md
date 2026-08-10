# Google Health API - Fitness Widget Setup

Integración con Google Health API para obtener datos de fitness (Fitbit) y mostrarlos en tu perfil de GitHub.

## 📋 Requisitos Previos

- Cuenta de Google con acceso a Google Health API
- Cuenta de Fitbit vinculada a tu cuenta de Google
- Python 3.8 o superior
- Acceso a Google Cloud Console

## 🚀 Configuración Inicial

### 1. Configurar Google Cloud Project

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o selecciona uno existente
3. Habilita **Google Health API**:
   - Menú → APIs & Services → Library
   - Busca "Google Health API"
   - Click en "Enable"

### 2. Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services → Credentials**
2. Click en **"Create Credentials" → "OAuth client ID"**
3. Si es la primera vez, configura la pantalla de consentimiento:
   - User Type: **External**
   - App name: `Fitness Widget`
   - User support email: tu email
   - Developer contact: tu email
4. Crear OAuth client ID:
   - Application type: **Desktop app**
   - Name: `Fitness Widget Desktop`
5. **Descargar el JSON** y guardarlo como `credentials.json` en este directorio

### 3. Agregar Usuario de Prueba

1. Ve a **APIs & Services → OAuth consent screen**
2. En la sección **Test users**, click en **"Add Users"**
3. Agrega tu email de Google (el que tiene Fitbit vinculado)
4. Click en **"Save"**

⚠️ **Importante**: Sin este paso, la autenticación fallará con error 403.

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 5. Ejecutar Setup OAuth2

```bash
python google_health_setup.py
```

Este script:
- Abrirá tu navegador para autorizar el acceso
- Te pedirá que inicies sesión con tu cuenta de Google
- Guardará el token en `token.json`

### 6. Probar la Integración

```bash
python update_fitness_widget.py
```

Esto obtendrá tus datos de fitness del mes actual y actualizará el README de tu perfil.

## 🔧 Configuración en GitHub Actions

### 1. Preparar el Token

Después de ejecutar `google_health_setup.py`, tendrás un archivo `token.json`. Copia su contenido completo.

### 2. Agregar Secret en GitHub

1. Ve a tu repositorio de perfil: `https://github.com/TU_USUARIO/TU_USUARIO`
2. Settings → Secrets and variables → Actions
3. Click en **"New repository secret"**
4. Name: `GOOGLE_HEALTH_TOKEN`
5. Value: Pega el contenido completo de `token.json`
6. Click en **"Add secret"**

### 3. Actualizar Workflow

Crea o actualiza `.github/workflows/profile-update.yml`:

```yaml
name: Update Profile

on:
  schedule:
    - cron: '0 0 * * *'  # Diario a las 00:00 UTC
  workflow_dispatch:

jobs:
  fitness-widget:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout profile repo
        uses: actions/checkout@v4
        with:
          repository: TU_USUARIO/TU_USUARIO
          path: profile-repo
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Checkout health API repo
        uses: actions/checkout@v4
        with:
          repository: TU_USUARIO/google-health-api-setup
          path: health-repo
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd health-repo
          pip install -r requirements.txt

      - name: Create token file
        run: |
          cd health-repo
          echo '${{ secrets.GOOGLE_HEALTH_TOKEN }}' > token.json

      - name: Update fitness widget
        run: |
          cd health-repo
          python update_fitness_widget.py

      - name: Commit and push changes
        run: |
          cd profile-repo
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add README.md
          git diff --quiet && git diff --staged --quiet || (git commit -m "chore: update fitness stats" && git push)
```

## 📊 Datos Disponibles

El widget muestra las siguientes métricas del mes actual:

- 👟 **Steps**: Pasos totales
- 🔥 **Calories**: Calorías quemadas
- 📏 **Distance**: Distancia recorrida (km)
- ⏱️ **Active Minutes**: Minutos de actividad

## 🔄 Renovación de Tokens

Los tokens de acceso expiran cada hora, pero el script los renueva automáticamente usando el `refresh_token`. El `refresh_token` es válido por 6 meses (si no se usa durante ese tiempo, expira).

Si el token expira:
1. Ejecuta nuevamente `python google_health_setup.py`
2. Actualiza el secret `GOOGLE_HEALTH_TOKEN` en GitHub

## 🐛 Troubleshooting

### Error: "Access blocked: Authorization Error"

**Causa**: Tu email no está en la lista de usuarios de prueba.

**Solución**:
1. Ve a Google Cloud Console → OAuth consent screen
2. Agrega tu email en "Test users"
3. Vuelve a ejecutar `python google_health_setup.py`

### Error: "Invalid grant: Token has been expired or revoked"

**Causa**: El refresh token expiró (6 meses sin uso).

**Solución**:
1. Elimina `token.json`
2. Ejecuta `python google_health_setup.py`
3. Actualiza el secret en GitHub

### Error: "No data points found"

**Causa**: No hay datos de Fitbit sincronizados.

**Solución**:
1. Abre la app de Fitbit
2. Fuerza una sincronización
3. Verifica que tu cuenta de Fitbit esté vinculada a Google
4. Espera unos minutos y vuelve a intentar

### Error: "API not enabled"

**Causa**: Google Health API no está habilitada en tu proyecto.

**Solución**:
1. Ve a Google Cloud Console
2. APIs & Services → Library
3. Busca "Google Health API"
4. Click en "Enable"

## 📚 Referencias

- [Google Health API Documentation](https://developers.google.com/health)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
- [Google Health API Codelab](https://developers.google.com/health/codelabs/make-your-first-api-call-using-oauth2-playground)

## 🔒 Seguridad

- **NUNCA** subas `credentials.json` o `token.json` a GitHub
- Usa GitHub Secrets para almacenar tokens
- El `.gitignore` ya está configurado para ignorar estos archivos
- Revoca el acceso en [Google Account Settings](https://myaccount.google.com/permissions) si ya no lo necesitas

## 📝 Notas

- Los datos provienen de Fitbit a través de Google Health API
- La API solo devuelve datos de ejercicio registrados
- Los datos se actualizan cuando Fitbit sincroniza con Google
- El widget muestra estadísticas del mes actual (desde el día 1)
