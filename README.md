# 🥐 Panadería POS

Punto de venta y dashboard de ventas para una panadería de barrio.
Proyecto de curso — **Redes e Infraestructura 2026** (1ª parte).

- **Arquitectura:** tres microservicios (FastAPI) accedidos por API REST, front-end en HTML/CSS/JS.
- **Dataset:** generado con `backend/dataset/generar_dataset.py` (semilla fija) para una panadería de barrio en Cali: 90 productos colombianos con precios en pesos, 3.200 clientes con datos completos y 94.758 ventas (2 ene 2025 – 15 nov 2026) con método de pago. Todo se vende por unidad.
- **Usuarios:** administrador (dashboard, catálogo, clientes, historial, usuarios) y cajeros (ventas con carrito). Cajeros del dataset: `mcastillo`, `jrengifo`, `lvalencia`, `dmosquera` (misma contraseña que `cajero`).
- **Despliegue:** dos servidores (back y front) + servidor DNS, con Vagrant y Ansible; acceso por el dominio `panaderia-pos.test`.
- **Documento de las fases de definición y diseño:** [`entrega/Panaderia_POS_Proyecto1.pdf`](entrega/Panaderia_POS_Proyecto1.pdf) (también en `.pptx`).

## Estructura

```
proyecto-panaderia-pos/
├── Vagrantfile               máquinas virtuales: dns-vm, back-vm, front-vm
├── ansible/
│   ├── site.yml              punto de entrada del despliegue
│   ├── dns.yml · back.yml · front.yml
│   ├── group_vars/all.yml    IPs, dominio, contraseñas iniciales
│   └── templates/            BIND9, Nginx y variables de entorno
├── systemd/                  un servicio por microservicio
├── backend/
│   ├── dataset/              CSV del dataset y el script que los genera
│   ├── database/             bases SQLite iniciales y su esquema SQL
│   ├── auth-service/         inicio de sesión (JWT) y usuarios         → puerto 8001
│   ├── catalog-service/      productos e historial de cambios          → puerto 8002
│   ├── sales-service/        clientes, ventas y métricas del dashboard → puerto 8003
│   ├── integration_tests/    pruebas con los tres servicios juntos
│   └── run_dev.py            levanta todo en el computador local
├── frontend/                 páginas del administrador y del cajero
└── entrega/                  presentación de las fases (PDF y PowerPoint)
```

Cada microservicio sigue la arquitectura en capas vista en clase:

```
<servicio>/
├── app/
│   ├── main.py               punto de ensamble
│   ├── api/                  rutas HTTP (presentación)
│   ├── application/          DTOs
│   ├── domain/               modelos, contratos (ABC) y reglas de negocio
│   └── infrastructure/       SQLite + SQLAlchemy, carga del dataset
├── tests/                    pruebas unitarias y de API
└── requirements.txt
```

## Despliegue con Vagrant

Requiere **VirtualBox 7.1+** y **Vagrant 2.4+** (también en Mac con chip Apple). No hace falta instalar Ansible: corre dentro de cada máquina.

```bash
vagrant up
```

| Máquina | IP | Nombre | Contenido |
|---|---|---|---|
| `dns-vm` | 192.168.56.10 | `ns.panaderia-pos.test` | BIND9 |
| `back-vm` | 192.168.56.12 | `api.panaderia-pos.test` | 3 microservicios + Nginx (API Gateway) |
| `front-vm` | 192.168.56.11 | `panaderia-pos.test` | Nginx + front-end |

### Acceso desde el computador cliente

El equipo debe preguntarle a `dns-vm` por el dominio del proyecto:

**Windows** (PowerShell como administrador):

```powershell
Add-DnsClientNrptRule -Namespace ".panaderia-pos.test", "panaderia-pos.test" -NameServers "192.168.56.10"
```

**Mac** (Terminal):

```bash
sudo mkdir -p /etc/resolver
echo "nameserver 192.168.56.10" | sudo tee /etc/resolver/panaderia-pos.test
```

Luego abrir **http://panaderia-pos.test**. Usuarios iniciales: `admin` y `cajero` (contraseñas en `ansible/group_vars/all.yml`).

| Qué | Dirección |
|---|---|
| Aplicación | http://panaderia-pos.test |
| Swagger auth | http://api.panaderia-pos.test/api/v1/auth/docs |
| Swagger catalog | http://api.panaderia-pos.test/api/v1/catalog/docs |
| Swagger sales | http://api.panaderia-pos.test/api/v1/sales/docs |

Comandos útiles:

```bash
vagrant provision back-vm    # volver a desplegar el back-end después de cambiar código
vagrant provision front-vm   # volver a desplegar el front-end
vagrant ssh back-vm          # entrar a una máquina
vagrant halt                 # apagar las máquinas
vagrant destroy -f           # borrarlas

# Volver a los datos originales del dataset (borra ventas, clientes, usuarios y cambios registrados)
vagrant ssh back-vm -c "sudo systemctl stop 'panaderia-*' && sudo sh -c 'rm -f /var/lib/panaderia-pos/*.db' && sudo systemctl start panaderia-auth-service panaderia-catalog-service panaderia-sales-service"
```

## Correr en el computador local

Requiere Python 3.10 o superior.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Mac / Linux
pip install -r requirements-dev.txt
python run_dev.py               # → http://127.0.0.1:8080
```

La primera vez cada servicio crea su base en `backend/<servicio>/` y la llena desde `backend/dataset` (unos segundos).

Para entrar, usa estos usuarios de desarrollo:

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin` | `admin12345` |
| Cajero | `mcastillo`, `jrengifo`, `lvalencia`, `dmosquera` o `cajero` | `cajero12345` |

Si ya habías corrido una versión anterior del proyecto, `run_dev.py` detecta las bases locales con el modelo viejo. Las guarda como `*_version_anterior_<fecha>.db` y crea unas nuevas, así que no hay que borrar nada a mano.

Las fotos de los productos están en `frontend/img/productos/<id>.jpg`. Para regenerarlas a partir de las cuadrículas `lote_NN.png`, corre `python frontend/img/recortar_fotos.py <carpeta>`.

## Pruebas

```bash
cd backend
cd catalog-service && python -m pytest && cd ..
cd auth-service    && python -m pytest && cd ..
cd sales-service   && python -m pytest && cd ..

# Integración (con "python run_dev.py --no-front" corriendo en otra terminal)
python -m pytest integration_tests -v
```

Resultado: **105 pruebas aprobadas** (97 unitarias y de API + 8 de integración).
