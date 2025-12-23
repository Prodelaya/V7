# 📚 Guía de Configuración - Retador v2.0

> **Para**: Usuarios y Operadores  
> **Última actualización**: Diciembre 2025

---

## 🎯 ¿Qué es este documento?

Esta guía te explica **todas las opciones de configuración** que puedes ajustar en Retador para personalizarlo según tus necesidades. No necesitas saber programar para entender las opciones.

---

## 📁 ¿Dónde se configura?

Todas las configuraciones se guardan en un archivo llamado **`.env`** que está en la carpeta principal del proyecto.

> 💡 **Consejo**: Hay un archivo `.env.example` que puedes copiar y renombrar a `.env`, luego editar los valores según tu caso.

---

## 🎰 Configuración de Casas de Apuestas

### 1️⃣ Casas a Consultar (API_BOOKMAKERS)

**¿Qué es?**  
Lista de TODAS las casas de apuestas de las que quieres recibir información de surebets.

**¿Para qué sirve?**  
El sistema consulta los odds de estas casas para encontrar oportunidades de apuesta segura.

**Ejemplo**:
```env
API_BOOKMAKERS=pinnaclesports,retabet_apuestas,yaasscasino,bet365
```

**Reglas**:
- Separa cada casa con una coma
- No uses espacios
- Incluye tanto las casas "sharp" (profesionales) como las casas donde tú apuestas

---

### 2️⃣ Casas Sharp (SHARP_BOOKMAKERS)

**¿Qué es?**  
Casas de apuestas profesionales que se usan como referencia.

**¿Para qué sirve?**  
Las odds de estas casas se consideran "verdaderas". Si otra casa tiene mejores odds que una sharp, es una oportunidad.

**Ejemplo**:
```env
SHARP_BOOKMAKERS=pinnaclesports
```

**Reglas**:
- Normalmente solo necesitas `pinnaclesports` (Pinnacle)
- Puedes añadir otras separándolas con comas
- Estas casas deben estar también en `API_BOOKMAKERS`

---

### 3️⃣ Casas Donde Apuestas (TARGET_BOOKIES)

**¿Qué es?**  
Las casas de apuestas donde tienes cuenta y donde realizas tus apuestas.

**¿Para qué sirve?**  
Solo recibirás alertas de apuestas que puedas hacer en estas casas.

**Ejemplo**:
```env
TARGET_BOOKIES=retabet_apuestas,yaasscasino
```

**Reglas**:
- Solo pon las casas donde REALMENTE puedes apostar
- Cada casa que pongas aquí necesita un canal de Telegram configurado
- Estas casas deben estar también en `API_BOOKMAKERS`

---

### 4️⃣ Canales de Telegram (BOOKMAKER_CHANNELS)

**¿Qué es?**  
Asociación entre cada casa de apuestas y el canal de Telegram donde llegarán las alertas.

**¿Para qué sirve?**  
Organiza las alertas: cada casa tiene su propio canal. Así puedes suscribirte solo a las casas que te interesan.

**Ejemplo**:
```env
BOOKMAKER_CHANNELS=retabet_apuestas=-1002294438792,yaasscasino=-1002360901387
```

**Formato**: `nombre_casa=ID_del_canal`

**¿Cómo obtener el ID del canal?**
1. Añade el bot `@getidsbot` a tu canal
2. Reenvía un mensaje del canal al bot
3. El bot te dará un número negativo (ej: `-1002294438792`)

---

### 5️⃣ Contrapartidas Permitidas (BOOKIE_CONTRAPARTIDAS) - Avanzado

**¿Qué es?**  
Define qué casas "sharp" son válidas como referencia para cada casa donde apuestas.

**¿Para qué sirve?**  
Filtrado avanzado. Por ejemplo: solo quieres recibir alertas de Retabet cuando la contrapartida sea Pinnacle.

**Ejemplo**:
```env
BOOKIE_CONTRAPARTIDAS=retabet_apuestas=pinnaclesports,yaasscasino=pinnaclesports|bet365
```

**Reglas**:
- Formato: `casa_donde_apuestas=casa_sharp1|casa_sharp2`
- Si no configuras esto, cualquier sharp es válido
- Es opcional - solo para usuarios avanzados

---

## 🔢 Configuración de Odds y Ganancias

### Odds Mínima y Máxima (MIN_ODDS / MAX_ODDS)

**¿Qué es?**  
Rango de cuotas que aceptas.

**¿Para qué sirve?**  
Filtra apuestas muy bajas (poco interesantes) o muy altas (sospechosas).

**Ejemplo**:
```env
MIN_ODDS=1.30
MAX_ODDS=10.0
```

---

### Ganancia Mínima y Máxima (MIN_PROFIT / MAX_PROFIT)

**¿Qué es?**  
Porcentaje de ganancia mínimo y máximo para considerar una surebet.

**¿Para qué sirve?**  
- `MIN_PROFIT`: Evita alertas de surebets con ganancia muy pequeña
- `MAX_PROFIT`: Evita alertas sospechosas (errores de odds)

**Ejemplo**:
```env
MIN_PROFIT=-1.0
MAX_PROFIT=25.0
```

> 📌 **Nota**: Un `MIN_PROFIT` negativo acepta surebets en ligera pérdida, útiles para bonos o freerolls.

---

## 🤖 Configuración de Telegram

### Token del Bot (TELEGRAM_BOT_TOKEN)

**¿Qué es?**  
Clave secreta para que el bot pueda enviar mensajes.

**¿Cómo obtenerlo?**
1. Habla con `@BotFather` en Telegram
2. Crea un nuevo bot con `/newbot`
3. Copia el token que te da

**Ejemplo**:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

---

## 🌐 Configuración de la API

### URL de la API (API_BASE_URL)

**¿Qué es?**  
Dirección del servidor que proporciona los datos de surebets.

**Ejemplo**:
```env
API_BASE_URL=https://api.example.com/api/v1
```

---

### Credenciales de API

**Ejemplo**:
```env
API_LOGIN=tu_usuario
API_PASSWORD=tu_contraseña
```

---

## 💾 Configuración de Redis

### Conexión a Redis (REDIS_URL)

**¿Qué es?**  
Redis es la base de datos que recuerda qué picks ya se enviaron para no repetirlos.

**Ejemplo**:
```env
REDIS_URL=redis://localhost:6379/0
```

---

## ⚙️ Otras Configuraciones

### Modo Debug (DEBUG)

**¿Qué es?**  
Activa mensajes detallados para encontrar problemas.

**Ejemplo**:
```env
DEBUG=false
```

---

### Tiempo de Vida del Caché (CACHE_TTL)

**¿Qué es?**  
Cuántos segundos se guarda información en memoria.

**Ejemplo**:
```env
CACHE_TTL=10
```

---

## 📋 Resumen Rápido

| Variable             | ¿Qué hace?           | Ejemplo                  |
| -------------------- | -------------------- | ------------------------ |
| `API_BOOKMAKERS`     | Casas a consultar    | `pinnaclesports,retabet` |
| `SHARP_BOOKMAKERS`   | Casas de referencia  | `pinnaclesports`         |
| `TARGET_BOOKIES`     | Casas donde apuestas | `retabet,yaasscasino`    |
| `BOOKMAKER_CHANNELS` | Canales de Telegram  | `retabet=-100123`        |
| `MIN_ODDS`           | Cuota mínima         | `1.30`                   |
| `MAX_ODDS`           | Cuota máxima         | `10.0`                   |
| `MIN_PROFIT`         | Ganancia mínima (%)  | `-1.0`                   |
| `MAX_PROFIT`         | Ganancia máxima (%)  | `25.0`                   |
| `TELEGRAM_BOT_TOKEN` | Token del bot        | `123:ABC...`             |
| `REDIS_URL`          | Conexión a Redis     | `redis://localhost`      |

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si me olvido de una variable?
El sistema usará valores por defecto, pero algunas variables son obligatorias (como el token de Telegram).

### ¿Puedo cambiar la configuración sin reiniciar?
No. Después de editar `.env`, debes reiniciar el servicio.

### ¿Dónde veo errores de configuración?
En los logs del sistema. Si algo está mal, verás un mensaje descriptivo al iniciar.

---

## 🆘 ¿Necesitas Ayuda?

Si tienes dudas sobre alguna configuración, puedes:
1. Revisar el archivo `.env.example` que incluye comentarios explicativos
2. Consultar la documentación técnica en `docs/09-Bookmakers-Configuration.md`
3. Contactar con soporte

---

> 📝 Este documento se actualizará conforme se añadan nuevas opciones de configuración.
