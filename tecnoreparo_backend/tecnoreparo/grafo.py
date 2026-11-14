"""Rede geográfica não direcionada; BFS e Dijkstra implementados no projeto."""
from dataclasses import asdict, dataclass
from math import asin, cos, inf, isfinite, radians, sin, sqrt

from .estruturas import Fila
from .modelos import ConflitoError, NaoEncontradoError, ValidacaoError


@dataclass(frozen=True)
class Ponto:
    id: str
    nome: str
    latitude: float
    longitude: float
    ordem_id: str | None = None


class GrafoRotas:
    """Dicionários de adjacência com pesos positivos em quilômetros."""

    def __init__(self):
        self._pontos: dict[str, Ponto] = {}
        self._adj: dict[str, dict[str, float]] = {}
        self._medidas: dict[frozenset, str] = {}
        self._proximo = 1

    @staticmethod
    def _numero(valor, campo, minimo, maximo):
        if type(valor) not in (int, float) or not isfinite(valor) or not minimo <= valor <= maximo:
            raise ValidacaoError(f"{campo} deve estar entre {minimo} e {maximo}.")
        return float(valor)

    def _ponto(self, identificador):
        if not isinstance(identificador, str) or identificador not in self._pontos:
            raise NaoEncontradoError("Local não encontrado na rede.")
        return self._pontos[identificador]

    def adicionar_ponto(self, nome, latitude, longitude, ordem_id=None):
        if not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 60:
            raise ValidacaoError("Nome do local deve ter de 1 a 60 caracteres.")
        lat = self._numero(latitude, "Latitude", -90, 90)
        lon = self._numero(longitude, "Longitude", -180, 180)
        if len(self._pontos) >= 40:
            raise ConflitoError("Esta rede demonstrativa aceita até 40 locais.")
        ponto = Ponto(f"P-{self._proximo:04d}", nome.strip(), lat, lon, ordem_id)
        self._pontos[ponto.id] = ponto
        self._adj[ponto.id] = {}
        self._proximo += 1
        return asdict(ponto)

    def remover_ponto(self, identificador):
        ponto = self._ponto(identificador)
        for vizinho in list(self._adj[identificador]):
            del self._adj[vizinho][identificador]
            del self._medidas[frozenset((identificador, vizinho))]
        del self._adj[identificador]
        del self._pontos[identificador]
        return asdict(ponto)

    @staticmethod
    def distancia_geografica(a, b):
        lat1, lat2 = radians(a.latitude), radians(b.latitude)
        dlat = lat2 - lat1
        dlon = radians(b.longitude - a.longitude)
        h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return 2 * 6371.0088 * asin(sqrt(min(1, max(0, h))))

    def conectar(self, origem, destino, distancia_km=None):
        a, b = self._ponto(origem), self._ponto(destino)
        if origem == destino:
            raise ValidacaoError("Escolha dois locais diferentes para a conexão.")
        medida = "geografica_aproximada" if distancia_km is None else "informada"
        distancia = self.distancia_geografica(a, b) if distancia_km is None else distancia_km
        distancia = self._numero(distancia, "Distância em km", 0.000001, 40075)
        if destino not in self._adj[origem] and len(self._medidas) >= 120:
            raise ConflitoError("Esta rede demonstrativa aceita até 120 conexões.")
        self._adj[origem][destino] = distancia
        self._adj[destino][origem] = distancia
        self._medidas[frozenset((origem, destino))] = medida
        return {"origem": origem, "destino": destino, "distancia_km": distancia, "medida": medida}

    def desconectar(self, origem, destino):
        self._ponto(origem)
        self._ponto(destino)
        if destino not in self._adj[origem]:
            raise NaoEncontradoError("Conexão não encontrada.")
        distancia = self._adj[origem].pop(destino)
        del self._adj[destino][origem]
        del self._medidas[frozenset((origem, destino))]
        return {"origem": origem, "destino": destino, "distancia_km": distancia}

    def alcancaveis(self, origem):
        """Busca em largura: O(V + E), usando a Fila da Unidade I."""
        self._ponto(origem)
        fila = Fila()
        fila.enfileirar(origem)
        vistos, percurso = {origem}, []
        while not fila.esta_vazia():
            atual = fila.desenfileirar()
            percurso.append(atual)
            for vizinho in self._adj[atual]:
                if vizinho not in vistos:
                    vistos.add(vizinho)
                    fila.enfileirar(vizinho)
        return percurso

    def menor_caminho(self, origem, destino):
        """Dijkstra com seleção linear: O(V² + E), sem heap ou biblioteca de grafos."""
        self._ponto(origem)
        self._ponto(destino)
        distancias = {ponto: inf for ponto in self._pontos}
        anteriores, visitados, percurso = {}, set(), []
        distancias[origem] = 0.0
        while len(visitados) < len(self._pontos):
            atual, melhor = None, inf
            for ponto in self._pontos:
                if ponto not in visitados and distancias[ponto] < melhor:
                    atual, melhor = ponto, distancias[ponto]
            if atual is None:
                break
            visitados.add(atual)
            percurso.append(atual)
            if atual == destino:
                break
            for vizinho, peso in self._adj[atual].items():
                tentativa = melhor + peso
                if tentativa < distancias[vizinho]:
                    distancias[vizinho] = tentativa
                    anteriores[vizinho] = atual
        encontrada = distancias[destino] != inf
        caminho = []
        if encontrada:
            atual = destino
            while True:
                caminho.append(atual)
                if atual == origem:
                    break
                atual = anteriores[atual]
            caminho.reverse()
        return {"origem": origem, "destino": destino, "encontrada": encontrada,
                "caminho": caminho, "locais": [asdict(self._pontos[p]) for p in caminho],
                "distancia_km": distancias[destino] if encontrada else None,
                "visitados_dijkstra": percurso, "alcancaveis_bfs": self.alcancaveis(origem),
                "algoritmo": "Dijkstra", "complexidade": "O(V² + E)",
                "aviso": "Melhor caminho apenas na rede cadastrada. Não representa trânsito ou ruas reais."}

    def estado(self):
        trechos = [{"origem": a, "destino": b, "distancia_km": peso,
                    "medida": self._medidas[frozenset((a, b))]}
                   for a, vizinhos in self._adj.items() for b, peso in vizinhos.items() if a < b]
        return {"pontos": [asdict(p) for p in self._pontos.values()], "trechos": trechos,
                "direcionado": False, "unidade": "km",
                "aviso": "Rede de conexões cadastradas; coordenadas geográficas não incluem ruas ou trânsito."}
