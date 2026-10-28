## Corrupción de memoria en el motor de PHP (request lifecycle) permite ejecución remota de código no autenticada (RCE) ##

*(CVE-2026-109618 y CVE-2026-109619, conocidas colectivamente como PHP2Shell)*

## Resumen
Dos vulnerabilidades críticas en el runtime de PHP permiten a un atacante remoto no autenticado ejecutar código arbitrario con los privilegios del proceso PHP (mod_php, PHP-FPM, php-cgi, etc.). Afectan a todas las instalaciones que sirven peticiones web (desde PHP 5.4 en adelante; solo las ramas 8.2–8.5 recibieron parches oficiales). Se explotan antes de que se ejecute el código de la aplicación, por lo que frameworks como WordPress, Drupal, Laravel, Joomla o Magento no ofrecen protección. Fueron parcheadas el 21 de octubre de 2026 y añadidas al catálogo KEV de CISA el 26 de octubre por evidencia de explotación en la naturaleza.

## Detalles técnicos
- **CWE**: CWE-416 (Use After Free). También relacionadas: CWE-755 (Improper Handling of Exceptional Conditions), CWE-824 (Access of Uninitialized Pointer) y otras asociadas a corrupción de estado interno.
- **Endpoint/Componente afectado**: Ciclo de vida de la petición en el motor de PHP (parsing de variables de request, manejo de out-of-memory y estado global/request-owned). Especialmente crítico en Apache con mod_php (explotación demostrada con una sola petición HTTP antes de que se ejecute código de aplicación). También afecta PHP-FPM, php-cgi, FrankenPHP y LiteSpeed.
- **Autenticación requerida**: Ninguna (no autenticada).
- **Entorno de pruebas**: PHP 8.x (versiones anteriores a 8.5.12 / 8.4.27 / 8.3.36 / 8.2.35) sirviendo peticiones web, preferiblemente con mod_php y límites de memoria por defecto o reducidos. Afecta también a versiones EOL (5.4–8.1) sin parche oficial.

## Pasos de reproducción
1. Identificar un servidor vulnerable que ejecute PHP no parcheado (comprobar versión con `phpinfo()` o cabeceras).
2. Enviar peticiones HTTP especialmente elaboradas (multipart o de gran tamaño) diseñadas para forzar un escenario de out-of-memory (OOM) mientras se inicializan estructuras internas de la request (CVE-2026-109618) o para dejar estado interno “stale” (use-after-free) que sobreviva a la liberación de memoria y sea reutilizado por una petición posterior del mismo worker (CVE-2026-109619, a menudo relacionada con `session.upload_progress` u otros paths de error fatal).
3. Observar ejecución de código con privilegios del worker PHP (por ejemplo, escritura de webshell o comandos del sistema). En entornos de laboratorio se ha confirmado RCE sobre mod_php con límites de memoria por defecto.

*(Nota: los detalles exactos de los payloads públicos varían según versión, SAPI y layout de memoria; no existe un único exploit universal 100 % fiable en todos los entornos.)*

## Impacto
Un atacante puede obtener una shell remota en el servidor web sin necesidad de credenciales. Esto permite:
- Comprometer completamente el sitio (robo de datos, defacement, instalación de malware/ransomware).
- Movimiento lateral hacia otros servicios o bases de datos.
- Exfiltración de secretos (tokens, claves, hashes de contraseñas) que puedan residir en memoria de otros workers.
- Impacto masivo en la infraestructura web mundial (PHP potencia ~70 % de los sitios). Ya se han observado intentos de explotación previos a la divulgación pública y actividad posterior a escala.

## Severidad (CVSS)
**CVSS v4.0: 9.2 (Critical)**  
Vector aproximado (según evaluación de PHP/CNA): AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N (o equivalente).  

Justificación: explotable de forma remota, sin autenticación ni interacción del usuario, impacto total en confidencialidad, integridad y disponibilidad del proceso PHP, y con evidencia de explotación en la naturaleza (CISA KEV).

## Recomendación de solución
**Causa raíz**: manejo incorrecto de condiciones excepcionales (OOM y errores fatales) que deja estructuras de request parcialmente inicializadas o estado interno apuntando a memoria liberada, permitiendo corrupción de memoria controlable por el atacante.

**Fix sugerido**:
- Actualizar inmediatamente a las versiones parcheadas:
  - PHP 8.5.12
  - PHP 8.4.27
  - PHP 8.3.36
  - PHP 8.2.35
- Reiniciar los workers/procesos PHP (Apache, PHP-FPM, etc.) después de la actualización.
- Para versiones EOL (≤ 8.1): migrar a una rama soportada o aplicar backports del distribuidor (si existen).
- Mitigaciones temporales incompletas (no sustituyen el parche): desactivar `session.upload_progress.enabled=0` y revisar límites de memoria, pero PHP afirma explícitamente que **no existen mitigaciones completas**.

Priorizar sistemas expuestos a Internet y realizar investigación forense de posibles compromisos previos (intentos detectados desde al menos el 17 de octubre de 2026).
