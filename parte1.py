import simpy
import random
import statistics

# Parámetros globales
NUM_RECEPCIONISTAS = 1
NUM_MEDICOS = 2
TIEMPO_REGISTRO_PROMEDIO = 2.0
TIEMPO_CONSULTA_PROMEDIO = 7.0
TASA_LLEGADA_PACIENTES = 5.0  # un paciente cada 5 min en promedio
TIEMPO_SIMULACION = 120.0

tiempos_de_espera_totales = []


def paciente(env, nombre, recepcionistas, medicos):
    tiempo_de_llegada = env.now
    # Registro
    with recepcionistas.request() as req:
        yield req
        duracion_registro = random.expovariate(1.0 / TIEMPO_REGISTRO_PROMEDIO)
        yield env.timeout(duracion_registro)
    # Consulta
    with medicos.request() as req:
        yield req
        duracion_consulta = random.expovariate(1.0 / TIEMPO_CONSULTA_PROMEDIO)
        yield env.timeout(duracion_consulta)

    tiempo_total = env.now - tiempo_de_llegada
    tiempos_de_espera_totales.append(tiempo_total)


def generador_pacientes(env, recepcionistas, medicos):
    i = 0
    while True:
        i += 1
        inter_arrival = random.expovariate(1.0 / TASA_LLEGADA_PACIENTES)
        yield env.timeout(inter_arrival)
        env.process(paciente(env, f"Paciente {i}", recepcionistas, medicos))


def correr_clinica():
    random.seed(42)
    env = simpy.Environment()

    recepcionistas = simpy.Resource(env, capacity=NUM_RECEPCIONISTAS)
    medicos = simpy.Resource(env, capacity=NUM_MEDICOS)

    env.process(generador_pacientes(env, recepcionistas, medicos))
    env.run(until=TIEMPO_SIMULACION)

    if tiempos_de_espera_totales:
        total_pacientes = len(tiempos_de_espera_totales)
        promedio = statistics.mean(tiempos_de_espera_totales)
        maximo = max(tiempos_de_espera_totales)
        print("=== Resultados clínica ===")
        print(f"Pacientes atendidos: {total_pacientes}")
        print(f"Tiempo promedio en clínica: {promedio:.2f} minutos")
        print(f"Tiempo máximo en clínica: {maximo:.2f} minutos")
    else:
        print("No se atendieron pacientes.")


if __name__ == "__main__":
    correr_clinica()
