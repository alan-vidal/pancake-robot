# Pancake-Robot
![pancake-robot](images/record/it4-prototipo.jpeg "pancake-robot")

**Pancake Robot** es una plataforma robótica de movimiento de dos ruedas que utiliza como base una [MicroPython Pyboard v1.1](https://micropython.org), el propósito es desarrollar un robot modular, que permita la fácil integración de partes y piezas según el propósito de cada equipo de desarrollo.

> [!NOTE]
> *El proyecto nacio como un ejercicio académico para mostrar un proceso de pototipado. El proyecto se encuentra en desarrollo, esta abierto a colaboración.*

## Stack
- [Micropython](https://micropython.org)
- [Fusion 360](https://www.autodesk.com/products/fusion-360/overview)

## Componentes
| Item | Cantidad |
| :--- | :---: |
|Pyboard v1.1 | 1 |
|Motores 1.2V | 2 |
|BRV8833 | 1 |
|MPU6050 | 1 |


## Estructura del Proyecto
```
$PANCAKE-ROBOT
│   # Archivos de codigo (MicroPython)
├── code
│   # Archivos de modelacion 3D
├── fusion-360
│   # Archivos de Corte Laser
├── dxf-file
│   # Archivos de Impresion 3D
└── stl-file
│   # Imagenes
└── images
```

## Licencia
[MIT License](LICENSE)
