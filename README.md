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
python -m unittest discover -s test
```

4. **Ejecutar la aplicacion** utilizando las linas de comando que siguen en distintas terminales de comando:

```bash
python src/start-server.py -H 0.0.0.0 -p 11111 -s serverfiles/
python src/upload.py -H 0.0.0.0 -p 11111
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
