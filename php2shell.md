# Use Memory Corruption en el motor de PHP (request lifecycle) permite RCE no autenticada (PHP2Shell)

> **CVE-2026-109618 / CVE-2026-109619**  
> Critical unauthenticated Remote Code Execution in PHP core

---

## 1. Resumen Ejecutivo

Dos vulnerabilidades críticas de seguridad de memoria (Use-After-Free y corrupción de estado interno) en el núcleo del motor PHP afectan al ciclo de vida de las peticiones HTTP.

- Afectan a **todas** las instalaciones de PHP que sirven requests web (mod_php, PHP-FPM, php-cgi, FrankenPHP, LiteSpeed…).
- Permiten RCE no autenticada con privilegios del proceso PHP worker.
- En muchos escenarios (especialmente mod_php) se puede explotar **antes** de que se ejecute código de la aplicación.
- Parcheadas el **21 de octubre de 2026**.
- Explotación activa confirmada e incluidas en **CISA KEV** el 26 de octubre de 2026.

---

## 2. Identificadores

| Campo                 | Valor |
|-----------------------|-------|
| **CVE**               | CVE-2026-109618, CVE-2026-109619 |
| **GHSA**              | [GHSA-w8hw-w9fx-j79w](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w) · [GHSA-6wmf-4rv5-p3rp](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp) |
| **CWE principal**     | CWE-416 (Use After Free) |
| **CWE secundarios**   | CWE-755, CWE-824, CWE-1325, CWE-1419 |
| **Nombre común**      | PHP2Shell / php2shell |
| **Otras referencias** | NVD, CISA KEV, advisory oficial PHP |

---

## 3. Detalles técnicos

| Campo                        | Valor |
|-----------------------------|-------|
| **CWE**                     | CWE-416 (principal) |
| **Componente afectado**     | Núcleo de PHP (request lifecycle / memory management / error handling) |
| **Versiones afectadas**     | < 8.2.35, < 8.3.36, < 8.4.27, < 8.5.12 (incluye 5.x–8.1) |
| **Versiones corregidas**    | 8.5.12, 8.4.27, 8.3.36, 8.2.35 |
| **Autenticación requerida** | No |
| **Vector de ataque**        | Red (AV:N) |
| **Complejidad de ataque**   | Alta (AC:H) |
| **Interacción del usuario** | No requerida (UI:N) |
| **Prerrequisitos**          | PHP sirviendo requests web. Mayor riesgo en `mod_php`. Mismo worker para el caso de stale state. |

---

## 4. Proof of Concept (PoC)

Para aprovecharnos de éste CVE, se procedió a explotarlo de manera controlada en un sitio aislado preparado unicamente con fines demostrativos.
<img width="1458" height="660" alt="imagen1pagweb" src="https://github.com/user-attachments/assets/13f78858-fe54-43bf-b0e4-7926f6cfbeff" />





---

## 5. Impacto

### Impacto técnico
- RCE no autenticada con privilegios del proceso PHP
- Posibilidad de pivot / movimiento lateral
- Fuga de información sensible (memoria de otros requests)

### Impacto de negocio
- Compromiso de datos (WordPress, Drupal, Joomla, Magento, etc.)
- Interrupción de servicio a gran escala
- Daño reputacional (“Black October”)
- Impacto normativo (GDPR, PCI-DSS…)

---

## 6. Severidad

**CVSS v4.0**

- **Vector**: `CVSS:4.0/AV:N/AC:H/AT:P/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N`
- **Puntuación**: **9.2 (Critical)**
- **Justificación**: RCE no autenticada sobre red con impacto total en C/I/A del proceso PHP.

**Otras métricas**
- **EPSS**: Extremadamente alto (~100 %)
- **CISA KEV**: Sí (añadidas el 26 de octubre de 2026)
- **Rating interno**: Crítica

---

## 7. Recomendación de solución

**Causa raíz**  
Manejo incorrecto de `longjmp()` en errores OOM y falta de reseteo completo de estado global (error, session, etc.) que apunta a memoria de requests previos.

**Fix definitivo**
- Actualizar a **PHP 8.5.12 / 8.4.27 / 8.3.36 / 8.2.35**
- Aplicar parches de distribución / LTS vendor
- Para 7.4 / 8.0 / 8.1: usar backports de código fuente o migrar

**Mitigaciones temporales** (reducen exposición pero **no** son completas):

- `session.upload_progress.enabled=0` + reiniciar workers
- `memory_limit=-1` (no overrideable) + límites bajos de `post_max_size`
- En PHP 8.5: `fatal_error_backtraces=0`
- Límites a nivel de web server / proxy
- Aislar sistemas que no puedan parchearse (especialmente ≤ 8.1)

**Prioridad de remediación**: **Crítica**

---

## 8. Detección e Indicadores de Compromiso (IoC)

- Requests HTTP anómalos (multipart crafted, intentos de forzar OOM)
- Logs de PHP / web server con errores fatales, OOM o crashes de workers
- Comportamiento anómalo de procesos PHP (comandos, conexiones salientes, archivos nuevos)
- Reglas Sigma publicadas por CISA
- Inventario completo de versiones de PHP (incluyendo embebido)

---

## 9. Timeline de divulgación

| Fecha       | Evento |
|-------------|--------|
| ≈ Ago 2026  | Descubrimiento (Calif / Wiz / OpenAI) |
| Sep 2026    | Coordinación de fix con PHP |
| 2026-10-17  | Intento de explotación en honeypot Amazon |
| 2026-10-20  | Fuga de IDs CVE y notice anticipado de PHP |
| 2026-10-21  | Publicación de parches y advisories GHSA |
| 2026-10-23  | Advisory informativo adicional (CVE-2026-115560) |
| 2026-10-26  | Inclusión en CISA KEV |
| 2026-10-28  | Estado actual: explotación activa confirmada |

---

## 10. Referencias

- [Advisory oficial PHP](https://www.php.net/archive/2026.php#2026-10-21-5)
- [GHSA-w8hw-w9fx-j79w](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w)
- [GHSA-6wmf-4rv5-p3rp](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp)
- [CISA Alert + KEV](https://www.cisa.gov/news-events/alerts/2026/10/21/critical-vulnerabilities-php-require-immediate-patching)


---

