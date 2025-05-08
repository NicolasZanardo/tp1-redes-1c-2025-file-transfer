# TP1 - Redes 1C 2025: File Transfer

Este repositorio contiene la entrega del primer Trabajo Práctico (TP1) de la materia **Redes de Computadoras** de la **Facultad de Ingeniería** de la **Universidad de Buenos Aires**.

## Instrucciones de instalación y ejecución de tests

1. **Ubicarse en la carpeta raíz** del proyecto.

2. **Instalar el proyecto en modo editable** ejecutando el siguiente comando:

```bash
pip install -e .
```

3. **Ejecutar los tests** utilizando:

```bash
python -m test.run [-vv] [-vq]
# Sin argumento para NORMAL logger
# -vv para VERBOSE logger
# -vq para QUIET logger
```

4. **Ejecutar la aplicacion** utilizando las linas de comando que siguen en distintas terminales de comando:

```bash
python3 ./src/start-server.py -H 0.0.0.0 -p 11111 -s ./serverfiles -v 
python3 ./src/upload.py -H 0.0.0.0 -p 11111 -s /home/damaris/clientfiles/prueba5M.txt -n file_udp.txt -v 
python3 ./src/download.py -H 0.0.0.0 -p 11111 -d /home/damaris/clientfiles/prueba5Mdownload.txt -n file_udp.txt -v 
```

## Como expandir el proyecto sin romper test o instalador

1. **Agregar archivo** `__init__.py` vacio a cada carpeta.

2. **Para agregar tests** 
    * **Siempre definir los test** dentro de una clase que herede `unittest.TestCase`.
    * **Los tests son metodos** que comienzan con `test_` dentro de la clase.

```python
import unittest

class TestSimple(unittest.TestCase):
    def test_true(self):
        self.assertTrue(True)
```
## Red virtual con mininet
Ejecutar la **topologia**
```bash
sudo mn --custom mytopo.py --topo mytopo
```
Iniciar cliente en h1 y server en h2
```bash
// sw
<mininet> h1 python3 ./src/start-server.py -H 10.0.0.1 -p 11111 -s ./serverfiles -v  > logfile 2> errorlogfile  & 
<mininet> h2 python3 ./src/upload.py -H 10.0.0.1 -p 11111 -s /home/damaris/clientfiles/prueba5M.txt -n file_udp.txt -v > logupload 2> errorlogupload 

<mininet> h2 python3 ./src/download.py -H 10.0.0.1 -p 11111 -d /home/damaris/clientfiles/prueba5Mdownload.txt -n file_udp.txt -v > logupload 2> errorlogupload 

// sr
<mininet> h1 python3 ./src/start-server.py -H 10.0.0.1 -p 11111 -s ./serverfiles -v -r sr > logfile 2> errorlogfile   & 
<mininet> h2 python3 ./src/upload.py -H 10.0.0.1 -p 11111 -s /home/damaris/clientfiles/prueba5M.txt -n file_udp.txt -v -r sr > logupload 2> errorlogupload 

<mininet> h2 python3 ./src/download.py -H 10.0.0.1 -p 11111 -d /home/damaris/clientfiles/prueba5Mdownload.txt -n file_udp.txt -v -r sr> logupload 2> errorlogupload 


```
Verificar inicialización
```bash
mininet> dump
```
Configurar **packet loss** (10%) y verificar con ping 
```bash
mininet> sh tc qdisc add dev s3-eth2 root netem loss 10%
```
Modificar **MTUs** de switches
```bash
mininet> sh ifconfig
mininet> sh ifconfig s2-eth2 mtu 1000
```
Generar trafico con **iperf** (con tamaño > MTU para generar **fragmentacion**)
```bash
// Udp
mininet> h2 iperf -s -u &
//Si el MTU es menor que 2000, el tráfico se fragmentará.
mininet> h1 iperf -c h2 -u -b 10M -l 2000 -t 5 

// Tcp
mininet> h2 iperf -s &                              
mininet> h1 iperf -c h2 -b 10M -M 1400 -t 5 
```

