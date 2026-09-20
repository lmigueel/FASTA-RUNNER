"""
FASTA RUNNER - Um jogo de plataforma para praticar bioinformática!
====================================================================
O jogador carrega um arquivo FASTA (contendo apenas A, C, G, T) e deve
pular sobre cada base nitrogenada da sequência apertando ESPAÇO.

Autor: Lucas Miguel de Carvalho, PhD
"""

import sys
import os
import re
import pygame

# CONFIGURAÇÕES GERAIS

LARGURA_TELA = 900
ALTURA_TELA = 500
FPS = 60

COR_FUNDO = (18, 20, 30)
COR_CHAO = (60, 45, 35)
COR_TEXTO = (240, 240, 240)
COR_TEXTO_DESTAQUE = (255, 215, 0)
COR_VIDA = (255, 80, 80)

# Cor de cada base nitrogenada
CORES_BASES = {
    "A": (80, 200, 120),   # verde  - Adenina
    "C": (80, 150, 255),   # azul   - Citosina
    "G": (255, 210, 60),   # amarelo- Guanina
    "T": (255, 90, 90),    # vermelho - Timina
}

CHAO_Y = ALTURA_TELA - 90
VELOCIDADE_JOGO = 6          # velocidade com que os obstáculos se movem
ESPACAMENTO_BASES = 220      # distância horizontal entre bases consecutivas
GRAVIDADE = 1.0
FORCA_PULO = -16.5

VIDAS_INICIAIS = 3

FONTE_NOME = None
FONTE_GRANDE = None
FONTE_MEDIA = None
FONTE_PEQUENA = None


# ETAPA A: LEITURA E VALIDAÇÃO DO ARQUIVO FASTA

class FastaInvalidoError(Exception):
    """Erro lançado quando o arquivo não é um FASTA válido (com A,C,G,T)."""
    pass


def ler_fasta(caminho_arquivo):
    """
    Lê e valida um arquivo FASTA contendo apenas as bases A, C, G, T.

    Retorna uma lista de tuplas (nome_da_sequencia, sequencia_str).
    Lança FastaInvalidoError se o arquivo não for um FASTA válido.
    """
    if not os.path.isfile(caminho_arquivo):
        raise FastaInvalidoError(f"Arquivo não encontrado: {caminho_arquivo}")

    with open(caminho_arquivo, "r", encoding="utf-8", errors="replace") as f:
        conteudo = f.read()

    if not conteudo.strip():
        raise FastaInvalidoError("O arquivo está vazio.")

    linhas = conteudo.splitlines()

    # Um FASTA válido deve começar (ignorando linhas em branco) com '>'
    primeira_linha_util = next((l for l in linhas if l.strip() != ""), None)
    if primeira_linha_util is None or not primeira_linha_util.startswith(">"):
        raise FastaInvalidoError(
            "O arquivo não parece ser um FASTA válido "
            "(a primeira linha deveria começar com '>')."
        )

    sequencias = []
    nome_atual = None
    bases_atual = []

    for linha in linhas:
        linha = linha.strip()
        if linha == "":
            continue
        if linha.startswith(">"):
            # Fecha a sequência anterior, se existir
            if nome_atual is not None:
                sequencias.append((nome_atual, "".join(bases_atual)))
            nome_atual = linha[1:].strip() or "sem_nome"
            bases_atual = []
        else:
            bases_atual.append(linha.upper())

    # Fecha a última sequência
    if nome_atual is not None:
        sequencias.append((nome_atual, "".join(bases_atual)))

    if not sequencias:
        raise FastaInvalidoError("Nenhuma sequência foi encontrada no arquivo.")

    # Validação estrita: primeira versão aceita somente A, C, G, T
    padrao_valido = re.compile(r"^[ACGT]+$")
    for nome, seq in sequencias:
        if seq == "":
            raise FastaInvalidoError(f"A sequência '{nome}' está vazia.")
        if not padrao_valido.match(seq):
            caracteres_invalidos = sorted(set(seq) - set("ACGT"))
            raise FastaInvalidoError(
                f"A sequência '{nome}' contém caracteres inválidos: "
                f"{', '.join(caracteres_invalidos)}. "
                "Esta versão do jogo aceita apenas as bases A, C, G, T."
            )

    return sequencias


# ETAPA B: O BONECO (JOGADOR)

class Jogador:
    """
    O boneco do jogador. Desenhado proceduralmente (sem precisar de
    arquivo de imagem externo) como um pequeno "cientista pixelado".
    """

    LARGURA = 46
    ALTURA = 60

    def __init__(self):
        self.x = 120
        self.y = CHAO_Y - self.ALTURA
        self.vel_y = 0.0
        self.no_chao = True
        self.perna_anim = 0.0

    @property
    def rect(self):
        # Hitbox um pouco menor que o desenho, para o jogo ser mais justo
        return pygame.Rect(self.x + 8, self.y + 6, self.LARGURA - 16, self.ALTURA - 10)

    def pular(self):
        if self.no_chao:
            self.vel_y = FORCA_PULO
            self.no_chao = False

    def atualizar(self):
        self.vel_y += GRAVIDADE
        self.y += self.vel_y
        if self.y >= CHAO_Y - self.ALTURA:
            self.y = CHAO_Y - self.ALTURA
            self.vel_y = 0
            self.no_chao = True
        if self.no_chao:
            self.perna_anim += 0.3

    def desenhar(self, tela):
        x, y = int(self.x), int(self.y)

        # Sombra
        sombra_largura = max(10, self.LARGURA - int(abs(self.vel_y)))
        pygame.draw.ellipse(
            tela, (0, 0, 0, 60),
            (x + (self.LARGURA - sombra_largura) // 2, CHAO_Y + 4, sombra_largura, 10)
        )

        # Pernas (com leve animação de "correndo" quando no chão)
        offset_perna = int(4 * abs(pygame.math.Vector2(1, 0).rotate(self.perna_anim * 40).x)) if self.no_chao else 0
        pygame.draw.rect(tela, (40, 60, 90), (x + 10, y + 42, 9, 18 - offset_perna))
        pygame.draw.rect(tela, (40, 60, 90), (x + 27, y + 42, 9, 18 + offset_perna if offset_perna < 10 else 18))

        # Corpo (jaleco de cientista)
        pygame.draw.rect(tela, (235, 235, 235), (x + 6, y + 20, self.LARGURA - 12, 26), border_radius=6)
        pygame.draw.rect(tela, (80, 150, 255), (x + 6, y + 20, self.LARGURA - 12, 8), border_radius=4)

        # Braços
        cor_braco = (235, 235, 235)
        pygame.draw.rect(tela, cor_braco, (x - 2, y + 24, 8, 16), border_radius=3)
        pygame.draw.rect(tela, cor_braco, (x + self.LARGURA - 6, y + 24, 8, 16), border_radius=3)

        # Cabeça
        pygame.draw.circle(tela, (255, 214, 170), (x + self.LARGURA // 2, y + 12), 13)

        # Óculos
        pygame.draw.circle(tela, (30, 30, 30), (x + self.LARGURA // 2 - 5, y + 12), 4, 2)
        pygame.draw.circle(tela, (30, 30, 30), (x + self.LARGURA // 2 + 5, y + 12), 4, 2)
        pygame.draw.line(tela, (30, 30, 30), (x + self.LARGURA // 2 - 1, y + 12),
                          (x + self.LARGURA // 2 + 1, y + 12), 2)
        # Cabelo
        pygame.draw.arc(tela, (90, 60, 40), (x + self.LARGURA // 2 - 13, y - 2, 26, 20), 3.4, 6.0, 4)


# ETAPA C/D: BASE NITROGENADA (OBSTÁCULO)

class BaseObstaculo:
    """Representa uma base nitrogenada (A, C, G ou T) que o jogador deve pular."""

    LADO = 42

    def __init__(self, letra, x):
        self.letra = letra
        self.x = float(x)
        self.y = CHAO_Y - self.LADO
        self.superada = False   # jogador já passou por cima com sucesso
        self.atingida = False   # jogador colidiu com ela

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.LADO, self.LADO)

    def atualizar(self):
        self.x -= VELOCIDADE_JOGO

    def desenhar(self, tela, fonte):
        cor = CORES_BASES.get(self.letra, (200, 200, 200))
        if self.atingida:
            cor = (100, 100, 100)
        rect = self.rect
        pygame.draw.rect(tela, cor, rect, border_radius=8)
        pygame.draw.rect(tela, (20, 20, 20), rect, width=2, border_radius=8)
        texto = fonte.render(self.letra, True, (20, 20, 20))
        tela.blit(
            texto,
            (rect.centerx - texto.get_width() // 2, rect.centery - texto.get_height() // 2),
        )


# CLASSE PRINCIPAL DO JOGO

class Jogo:
    def __init__(self, sequencias):
        self.sequencias = sequencias  # lista de (nome, seq)
        self.indice_sequencia = 0
        self.vidas = VIDAS_INICIAIS
        self.pontuacao = 0
        self.estado = "jogando"  # jogando | vitoria | derrota
        self.jogador = Jogador()
        self.obstaculos = []
        self.indice_proxima_base = 0
        self.distancia_percorrida = 0
        self.mensagem_final = ""
        self._carregar_sequencia_atual()

    # Preparação de cada sequência 
    def _carregar_sequencia_atual(self):
        self.jogador = Jogador()
        self.obstaculos = []
        self.indice_proxima_base = 0
        self.distancia_percorrida = 0
        nome, seq = self.sequencias[self.indice_sequencia]
        x_inicial = LARGURA_TELA + 200
        for i, base in enumerate(seq):
            x = x_inicial + i * ESPACAMENTO_BASES
            self.obstaculos.append(BaseObstaculo(base, x))

    @property
    def nome_sequencia_atual(self):
        return self.sequencias[self.indice_sequencia][0]

    @property
    def seq_atual(self):
        return self.sequencias[self.indice_sequencia][1]

    # Lógica de atualização 
    def processar_pulo(self):
        if self.estado == "jogando":
            self.jogador.pular()

    def atualizar(self):
        if self.estado != "jogando":
            return

        self.jogador.atualizar()
        rect_jogador = self.jogador.rect

        todos_superados = True
        for obs in self.obstaculos:
            obs.atualizar()

            if not obs.superada and not obs.atingida:
                todos_superados = False
                # Colisão: jogador bateu na base
                if rect_jogador.colliderect(obs.rect):
                    obs.atingida = True
                    self.vidas -= 1
                    if self.vidas <= 0:
                        self.estado = "derrota"
                        self.mensagem_final = (
                            "Você esbarrou em bases demais...\n"
                            "Tente novamente, futuro bioinformata!"
                        )
                        return
                # Passou com sucesso (o obstáculo já ficou atrás do jogador)
                elif obs.rect.right < rect_jogador.left:
                    obs.superada = True
                    self.pontuacao += 10

            if obs.atingida and obs.rect.right < rect_jogador.left - 5:
                obs.atingida = False  # já processado, evita recontagem
                obs.superada = True

        # Verifica se toda a sequência foi concluída (todas as bases ficaram
        # para trás, superadas ou atingidas)
        todas_para_tras = all(o.rect.right < 0 or o.superada or o.x < rect_jogador.x for o in self.obstaculos)
        if self.obstaculos and all((o.superada or o.atingida) for o in self.obstaculos):
            self._avancar_sequencia()

    def _avancar_sequencia(self):
        if self.indice_sequencia + 1 < len(self.sequencias):
            self.indice_sequencia += 1
            self._carregar_sequencia_atual()
        else:
            self.estado = "vitoria"
            self.mensagem_final = "Parabéns, Padawan da Bioinformática.\nVocê chegou até o fim!"

    # Desenho 
    def desenhar(self, tela):
        tela.fill(COR_FUNDO)

        # Chão
        pygame.draw.rect(tela, COR_CHAO, (0, CHAO_Y, LARGURA_TELA, ALTURA_TELA - CHAO_Y))
        pygame.draw.line(tela, (100, 80, 60), (0, CHAO_Y), (LARGURA_TELA, CHAO_Y), 3)

        # Obstáculos (bases)
        for obs in self.obstaculos:
            if -50 < obs.x < LARGURA_TELA + 50:
                obs.desenhar(tela, FONTE_MEDIA)

        # Jogador
        self.jogador.desenhar(tela)

        # HUD 
        # Nome da sequência no canto superior direito (item C do pedido)
        texto_nome = FONTE_MEDIA.render(f"Sequência: {self.nome_sequencia_atual}", True, COR_TEXTO_DESTAQUE)
        tela.blit(texto_nome, (LARGURA_TELA - texto_nome.get_width() - 20, 16))

        # Progresso na sequência
        progresso = sum(1 for o in self.obstaculos if o.superada or o.atingida)
        texto_progresso = FONTE_PEQUENA.render(
            f"Base {min(progresso + 1, len(self.obstaculos))}/{len(self.obstaculos)}", True, COR_TEXTO
        )
        tela.blit(texto_progresso, (LARGURA_TELA - texto_progresso.get_width() - 20, 50))

        # Sequência geral (X de Y sequências do arquivo)
        texto_seq_geral = FONTE_PEQUENA.render(
            f"Sequência {self.indice_sequencia + 1}/{len(self.sequencias)}", True, COR_TEXTO
        )
        tela.blit(texto_seq_geral, (LARGURA_TELA - texto_seq_geral.get_width() - 20, 74))

        # Vidas (canto superior esquerdo)
        texto_vidas = FONTE_MEDIA.render("Vidas: " + "♥ " * self.vidas, True, COR_VIDA)
        tela.blit(texto_vidas, (20, 16))

        # Pontuação
        texto_pontos = FONTE_PEQUENA.render(f"Pontos: {self.pontuacao}", True, COR_TEXTO)
        tela.blit(texto_pontos, (20, 50))

        # Instrução
        texto_instrucao = FONTE_PEQUENA.render("Pressione ESPAÇO para pular", True, (180, 180, 180))
        tela.blit(texto_instrucao, (20, ALTURA_TELA - 30))

        if self.estado == "vitoria":
            self._desenhar_tela_final(tela, COR_TEXTO_DESTAQUE)
        elif self.estado == "derrota":
            self._desenhar_tela_final(tela, COR_VIDA)

    def _desenhar_tela_final(self, tela, cor):
        overlay = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        tela.blit(overlay, (0, 0))

        linhas = self.mensagem_final.split("\n")
        y = ALTURA_TELA // 2 - (len(linhas) * 24)
        for linha in linhas:
            texto = FONTE_GRANDE.render(linha, True, cor)
            tela.blit(texto, (LARGURA_TELA // 2 - texto.get_width() // 2, y))
            y += 48

        texto_extra = FONTE_PEQUENA.render(
            "Pressione R para reiniciar ou ESC para sair", True, COR_TEXTO
        )
        tela.blit(texto_extra, (LARGURA_TELA // 2 - texto_extra.get_width() // 2, y + 20))


# TELA DE CARREGAMENTO / SELEÇÃO DE ARQUIVO (SEM DEPENDÊNCIAS EXTRAS)

def tela_carregar_arquivo(tela, clock):
    """
    Tela simples onde o usuário digita o caminho do arquivo FASTA.
    Retorna a lista de sequências validadas, ou None se o usuário sair.
    """
    caminho_digitado = ""
    mensagem_erro = ""
    ativo = True

    while ativo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return None
                elif evento.key == pygame.K_RETURN:
                    caminho = caminho_digitado.strip().strip('"').strip("'")
                    try:
                        sequencias = ler_fasta(caminho)
                        return sequencias
                    except FastaInvalidoError as e:
                        mensagem_erro = str(e)
                    except Exception as e:
                        mensagem_erro = f"Erro inesperado: {e}"
                elif evento.key == pygame.K_BACKSPACE:
                    caminho_digitado = caminho_digitado[:-1]
                else:
                    if evento.unicode and evento.unicode.isprintable():
                        caminho_digitado += evento.unicode

        tela.fill(COR_FUNDO)

        titulo = FONTE_GRANDE.render("FASTA RUNNER", True, COR_TEXTO_DESTAQUE)
        tela.blit(titulo, (LARGURA_TELA // 2 - titulo.get_width() // 2, 60))

        subtitulo = FONTE_PEQUENA.render(
            "Digite o caminho do arquivo FASTA (.fasta / .fa / .txt) e pressione ENTER",
            True, COR_TEXTO,
        )
        tela.blit(subtitulo, (LARGURA_TELA // 2 - subtitulo.get_width() // 2, 160))

        # Caixa de texto
        caixa_rect = pygame.Rect(LARGURA_TELA // 2 - 300, 210, 600, 44)
        pygame.draw.rect(tela, (30, 32, 45), caixa_rect, border_radius=6)
        pygame.draw.rect(tela, (100, 100, 130), caixa_rect, width=2, border_radius=6)
        texto_caixa = FONTE_MEDIA.render(caminho_digitado or "ex: sequencias.fasta", True,
                                          COR_TEXTO if caminho_digitado else (120, 120, 120))
        tela.blit(texto_caixa, (caixa_rect.x + 10, caixa_rect.y + 8))

        if mensagem_erro:
            linhas_erro = _quebrar_texto(mensagem_erro, FONTE_PEQUENA, 700)
            y_erro = 280
            for linha in linhas_erro:
                texto_erro = FONTE_PEQUENA.render(linha, True, COR_VIDA)
                tela.blit(texto_erro, (LARGURA_TELA // 2 - texto_erro.get_width() // 2, y_erro))
                y_erro += 24

        ajuda = FONTE_PEQUENA.render("ESC para sair", True, (140, 140, 140))
        tela.blit(ajuda, (LARGURA_TELA // 2 - ajuda.get_width() // 2, ALTURA_TELA - 40))

        pygame.display.flip()
        clock.tick(FPS)


def _quebrar_texto(texto, fonte, largura_max):
    palavras = texto.split(" ")
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        teste = (linha_atual + " " + palavra).strip()
        if fonte.size(teste)[0] <= largura_max:
            linha_atual = teste
        else:
            linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    return linhas


# LOOP PRINCIPAL

def main():
    global FONTE_GRANDE, FONTE_MEDIA, FONTE_PEQUENA

    pygame.init()
    pygame.display.set_caption("FASTA Runner - Aventura da Bioinformática")
    tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
    clock = pygame.time.Clock()

    FONTE_GRANDE = pygame.font.SysFont("arial", 34, bold=True)
    FONTE_MEDIA = pygame.font.SysFont("arial", 22, bold=True)
    FONTE_PEQUENA = pygame.font.SysFont("arial", 18)

    # Se o caminho do arquivo foi passado como argumento de linha de comando,
    # tenta usá-lo diretamente; caso contrário, mostra a tela de carregamento.
    sequencias = None
    if len(sys.argv) > 1:
        try:
            sequencias = ler_fasta(sys.argv[1])
        except FastaInvalidoError as e:
            print(f"Erro no arquivo FASTA: {e}")

    if sequencias is None:
        sequencias = tela_carregar_arquivo(tela, clock)

    if sequencias is None:
        pygame.quit()
        return

    jogo = Jogo(sequencias)
    rodando = True

    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    jogo.processar_pulo()
                elif evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key == pygame.K_r and jogo.estado != "jogando":
                    jogo = Jogo(sequencias)

        jogo.atualizar()
        jogo.desenhar(tela)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
