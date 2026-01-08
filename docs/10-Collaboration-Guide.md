# 🤝 Guía de Colaboración - Retador V7

## Repositorio
- **URL**: https://github.com/Prodelaya/V7
- **Rama principal**: `main`

---

## 👥 División del Trabajo

| Desarrollador  | Áreas              | Carpetas                                                                               |
| -------------- | ------------------ | -------------------------------------------------------------------------------------- |
| **Pablo** (tú) | Core, Backend      | `src/application/`, `src/config/`, `src/domain/`, `src/infrastructure/`, `src/shared/` |
| **Tu amigo**   | Web, Subscriptions | `src/subscriptions/`, `src/web/`                                                       |

---

## 🔐 Configuración Inicial (Solo una vez)

### 1. Pablo: Añadir colaborador en GitHub
1. Ir a https://github.com/Prodelaya/V7/settings/access
2. Click **"Add people"**
3. Buscar el usuario de tu amigo
4. Seleccionar rol: **Write** (puede hacer push)
5. Enviar invitación

### 2. Tu amigo: Aceptar y clonar
```bash
# 1. Aceptar invitación en email o en https://github.com/notifications

# 2. Clonar el repo
git clone https://github.com/Prodelaya/V7.git
cd V7

# 3. Configurar identidad
git config user.name "NombreAmigo"
git config user.email "email@ejemplo.com"

# 4. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Copiar y configurar .env
cp .env.example .env
# Editar .env con valores de desarrollo
```

---

## 🔄 Flujo de Trabajo Diario

### ✅ Enfoque Simple: Ambos en `main`

Dado que trabajan en **carpetas completamente separadas**, no necesitan ramas. Pueden trabajar directamente en `main`.

### Para tu amigo (ANTES de empezar a trabajar):
```bash
# 1. SIEMPRE hacer pull primero
git pull origin main

# 2. Trabajar en sus archivos (src/web/, src/subscriptions/)

# 3. Añadir cambios
git add src/web/ src/subscriptions/
# O específicamente:
git add src/web/templates/index.html

# 4. Commit con mensaje descriptivo
git commit -m "feat(web): añadir página de precios"

# 5. Push
git push origin main
```

### Para ti (Pablo):
```bash
# Tu flujo normal
git pull origin main  # Recomendado antes de empezar
# ... trabajar en src/domain/, src/config/, etc ...
git add .
git commit -m "feat(domain): implementar validator X"
git push origin main
```

---

## ⚠️ Reglas de Oro

### 1. **SIEMPRE hacer `git pull` antes de empezar**
```bash
git pull origin main
```
Esto evita el 99% de conflictos.

### 2. **No tocar carpetas del otro**
- Tu amigo **SOLO** modifica: `src/web/`, `src/subscriptions/`
- Tú **NO** modificas esas carpetas

### 3. **Commits pequeños y frecuentes**
- ❌ Un commit gigante con 50 archivos
- ✅ Varios commits pequeños y descriptivos

### 4. **Mensajes de commit claros**
```bash
# Formato sugerido
tipo(área): descripción corta

# Ejemplos:
git commit -m "feat(web): añadir formulario de contacto"
git commit -m "fix(web): corregir CSS en móvil"
git commit -m "style(web): mejorar colores del footer"
```

---

## 🚨 Si Hay Conflicto

En el raro caso de que haya conflicto (ambos modificaron el mismo archivo):

```bash
# 1. Git avisará del conflicto en push
git pull origin main

# 2. Abrir archivo conflictivo, buscar marcadores:
<<<<<<< HEAD
tu versión
=======
versión del otro
>>>>>>> origin/main

# 3. Editar manualmente, elegir qué mantener

# 4. Guardar, añadir y continuar
git add archivo_conflictivo
git commit -m "fix: resolver conflicto en X"
git push origin main
```

---

## 📋 Checklist Diario

### Tu amigo:
- [ ] `git pull origin main` (ANTES de empezar)
- [ ] Trabajar solo en `src/web/` y `src/subscriptions/`
- [ ] Commits pequeños con mensajes claros
- [ ] `git push origin main` al terminar

### Tú (Pablo):
- [ ] `git pull origin main` (ocasional, para ver cambios de él)
- [ ] Trabajar en tus áreas
- [ ] Push cuando termines

---

## 🛠️ Comandos Útiles

```bash
# Ver estado actual
git status

# Ver últimos commits
git log --oneline -10

# Ver qué archivos cambiaron en el último pull
git diff HEAD~1 --stat

# Descartar cambios locales de un archivo
git checkout -- archivo.py

# Ver ramas remotas
git branch -a
```

---

## 📞 Comunicación

- **Antes de modificar** algo fuera de tu área → Avisar al otro
- **Si hay error raro** → Compartir screenshot del error
- **Antes de cambios grandes** → Discutir primero

---

## 🚀 Resumen

1. **Pablo añade a su amigo** como colaborador en GitHub
2. **Amigo acepta** y clona el repo
3. **Ambos trabajan en `main`** porque sus áreas no se cruzan
4. **Regla #1**: `git pull` antes de empezar siempre
5. **Sin conflictos** porque cada uno tiene sus carpetas
