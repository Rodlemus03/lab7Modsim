import simpy
import random
import numpy as np
import statistics

# Parámetros del mundo y población
NUM_AGENTES = 50
ANCHO_MUNDO = 100.0
ALTO_MUNDO = 100.0

# DS interno (energía)
ENERGIA_MAX = 10.0
TASA_RECUPERACION_NATURAL = 0.2
GASTO_POR_MOVIMIENTO = 0.3
EFECTO_INTERACCION = 0.4

# DES estación de recarga
NUM_PUESTOS_RECARGA = 5
ENERGIA_CRITICA = 2.0
TIEMPO_RECARGA = 10.0

# Simulación
TIEMPO_SIMULACION = 200.0
DT = 1.0
RADIO_INTERACCION = 10.0


class Agente:
    def __init__(self, agente_id, posicion_inicial, env, estacion_recarga):
        self.id = agente_id
        self.env = env
        self.estacion_recarga = estacion_recarga

        self.posicion = np.array(posicion_inicial, dtype=float)
        angulo = random.uniform(0, 2 * np.pi)
        velocidad_mod = random.uniform(0.5, 1.5)
        self.velocidad = np.array(
            [np.cos(angulo) * velocidad_mod, np.sin(angulo) * velocidad_mod],
            dtype=float
        )

        self.energia = ENERGIA_MAX
        self.recargando = False
        self.recargas_realizadas = 0

    def proceso_recarga(self):
        self.recargando = True
        with self.estacion_recarga.request() as req:
            yield req
            yield self.env.timeout(TIEMPO_RECARGA)
            self.energia = ENERGIA_MAX
            self.recargas_realizadas += 1
        self.recargando = False

    def actualizar_estado(self, efecto_interaccion):
        if not self.recargando:
            flujo_in = TASA_RECUPERACION_NATURAL + efecto_interaccion
            flujo_out = GASTO_POR_MOVIMIENTO
            self.energia += (flujo_in - flujo_out) * DT
            self.energia = max(0.0, min(ENERGIA_MAX, self.energia))

            self.posicion += self.velocidad * DT
            self._manejar_bordes()

            if self.energia < ENERGIA_CRITICA and not self.recargando:
                self.env.process(self.proceso_recarga())

    def _manejar_bordes(self):
        if self.posicion[0] < 0:
            self.posicion[0] = 0
            self.velocidad[0] *= -1
        elif self.posicion[0] > ANCHO_MUNDO:
            self.posicion[0] = ANCHO_MUNDO
            self.velocidad[0] *= -1

        if self.posicion[1] < 0:
            self.posicion[1] = 0
            self.velocidad[1] *= -1
        elif self.posicion[1] > ALTO_MUNDO:
            self.posicion[1] = ALTO_MUNDO
            self.velocidad[1] *= -1


def ejecutar_simulacion(env, agentes, estacion_recarga, metricas):
    while env.now < TIEMPO_SIMULACION:
        efectos = [0.0 for _ in agentes]

        # Interacciones MBA
        for i in range(len(agentes)):
            for j in range(i + 1, len(agentes)):
                ai = agentes[i]
                aj = agentes[j]
                dist = np.linalg.norm(ai.posicion - aj.posicion)
                if dist <= RADIO_INTERACCION:
                    delta = EFECTO_INTERACCION
                    if random.random() < 0.5:
                        delta *= -1
                    efectos[i] += delta
                    efectos[j] += delta

        # Actualizar agentes (MBA + DS + DES)
        for idx, agente in enumerate(agentes):
            agente.actualizar_estado(efectos[idx])

        # Métricas
        energia_promedio = statistics.mean(a.energia for a in agentes)
        en_cola = len(estacion_recarga.queue)
        en_servicio = estacion_recarga.count
        metricas["tiempos"].append(env.now)
        metricas["energia_promedio"].append(energia_promedio)
        metricas["cola_recarga"].append(en_cola)
        metricas["en_servicio"].append(en_servicio)

        yield env.timeout(DT)


def correr_modelo_hibrido():
    random.seed(42)
    np.random.seed(42)

    env = simpy.Environment()
    estacion_recarga = simpy.Resource(env, capacity=NUM_PUESTOS_RECARGA)

    agentes = []
    for i in range(NUM_AGENTES):
        x = random.uniform(0, ANCHO_MUNDO)
        y = random.uniform(0, ALTO_MUNDO)
        agentes.append(Agente(i, (x, y), env, estacion_recarga))

    metricas = {
        "tiempos": [],
        "energia_promedio": [],
        "cola_recarga": [],
        "en_servicio": []
    }

    env.process(ejecutar_simulacion(env, agentes, estacion_recarga, metricas))
    env.run(until=TIEMPO_SIMULACION)

    total_recargas = sum(a.recargas_realizadas for a in agentes)
    energia_promedio_global = statistics.mean(metricas["energia_promedio"])
    cola_promedio = statistics.mean(metricas["cola_recarga"])

    print("=== Resultados modelo híbrido ===")
    print(f"Total de recargas realizadas: {total_recargas}")
    print(f"Energía promedio global: {energia_promedio_global:.2f}")
    print(f"Longitud promedio de cola de recarga: {cola_promedio:.2f}")
    print(f"Máxima cola observada: {max(metricas['cola_recarga'])}")
    print(f"Número máximo de agentes en servicio a la vez: {max(metricas['en_servicio'])}")


if __name__ == "__main__":
    correr_modelo_hibrido()
