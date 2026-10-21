class NoTrie:
    def __init__(self, trecho=""):
        self.trecho = trecho
        self.filhos = {}
        self.ids = []


class TrieCompacta:
    def __init__(self):
        self.raiz = NoTrie()

    def inserir(self, chave, entregadorId):
        noAtual = self.raiz
        restante = chave
        while restante:
            filho = noAtual.filhos.get(restante[0])
            if filho is None:
                filho = NoTrie(restante)
                filho.ids.append(entregadorId)
                noAtual.filhos[restante[0]] = filho
                return
            tamanhoComum = 0
            while (tamanhoComum < min(len(restante), len(filho.trecho))
                   and restante[tamanhoComum] == filho.trecho[tamanhoComum]):
                tamanhoComum += 1
            if tamanhoComum < len(filho.trecho):
                intermediario = NoTrie(filho.trecho[:tamanhoComum])
                noAtual.filhos[restante[0]] = intermediario
                filho.trecho = filho.trecho[tamanhoComum:]
                intermediario.filhos[filho.trecho[0]] = filho
                filho = intermediario
            restante = restante[tamanhoComum:]
            noAtual = filho
        noAtual.ids.append(entregadorId)

    def buscarPrefixo(self, prefixo):
        noAtual = self.raiz
        restante = prefixo
        while restante:
            filho = noAtual.filhos.get(restante[0])
            if filho is None:
                return []
            # O prefixo pode terminar no meio de uma aresta compactada.
            if filho.trecho.startswith(restante):
                noAtual = filho
                break
            if not restante.startswith(filho.trecho):
                return []
            restante = restante[len(filho.trecho):]
            noAtual = filho
        resultado = []
        pilha = [noAtual]
        while pilha:
            noAtual = pilha.pop()
            resultado.extend(noAtual.ids)
            pilha.extend(noAtual.filhos.values())
        return resultado
