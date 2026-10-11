/* Animações de resultado: roleta, caça-níquel, dado e poste do bicho.
   O servidor já decidiu o resultado; aqui só se encena a revelação.
   Sem JavaScript, ou com "reduzir movimento" ativado, o resultado aparece direto. */
(function () {
  "use strict";

  var reduzir = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function revelar(bloco) {
    if (bloco) bloco.classList.add("revelado");
  }

  function aleatorio(lista) {
    return lista[Math.floor(Math.random() * lista.length)];
  }

  /* ---- Roleta: roda desenhada em SVG, gira até a casa sorteada ---- */
  function construirRoda(svg, ordem) {
    var NS = "http://www.w3.org/2000/svg";
    var fatia = 360 / ordem.length;
    var R = 100, r = 64;
    var cores = { vermelho: "#c62828", preto: "#1b1b1b", verde: "#2e7d32" };

    function ponto(raio, graus) {
      var a = (graus - 90) * Math.PI / 180;
      return [(raio * Math.cos(a)).toFixed(3), (raio * Math.sin(a)).toFixed(3)];
    }
    function circulo(raio, cor) {
      var c = document.createElementNS(NS, "circle");
      c.setAttribute("r", raio);
      c.setAttribute("fill", cor);
      svg.appendChild(c);
    }

    circulo(109, "#4a2c12");
    circulo(104, "#d4a017");
    ordem.forEach(function (par, i) {
      var a0 = i * fatia - fatia / 2, a1 = a0 + fatia;
      var p0 = ponto(R, a0), p1 = ponto(R, a1), q1 = ponto(r, a1), q0 = ponto(r, a0);
      var caminho = document.createElementNS(NS, "path");
      caminho.setAttribute("d", "M" + p0 + " A" + R + " " + R + " 0 0 1 " + p1 + " L" + q1 + " A" + r + " " + r + " 0 0 0 " + q0 + " Z");
      caminho.setAttribute("fill", cores[par[1]]);
      caminho.setAttribute("stroke", "#d4a017");
      caminho.setAttribute("stroke-width", "0.7");
      svg.appendChild(caminho);
      var texto = document.createElementNS(NS, "text");
      texto.textContent = par[0];
      texto.setAttribute("transform", "rotate(" + (i * fatia) + ")");
      texto.setAttribute("y", -R + 13);
      texto.setAttribute("text-anchor", "middle");
      texto.setAttribute("fill", "#f6e7a6");
      texto.setAttribute("font-size", "9.5");
      texto.setAttribute("font-weight", "700");
      texto.setAttribute("font-family", "Courier New, monospace");
      svg.appendChild(texto);
    });
    circulo(r - 1, "#3b2a1a");
    circulo(24, "#d4a017");
    circulo(9, "#4a2c12");
  }

  var roda = document.querySelector("[data-roleta]");
  if (roda) {
    var ordem = JSON.parse(document.getElementById("roleta-ordem").textContent);
    var numeroSorteado = parseInt(roda.dataset.roleta, 10);
    var indice = ordem.map(function (par) { return par[0]; }).indexOf(numeroSorteado);
    var fatiaGraus = 360 / ordem.length;
    var disco = roda.querySelector(".roda-disco");
    var bola = roda.querySelector(".roda-bola");
    var bloco = roda.closest(".resultado");
    construirRoda(disco, ordem);
    var repouso = -(indice * fatiaGraus);
    if (reduzir) {
      disco.style.transform = "rotate(" + repouso + "deg)";
      revelar(bloco);
    } else {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          disco.classList.add("girando");
          bola.classList.add("girando");
          disco.style.transform = "rotate(" + (repouso - 360 * 5) + "deg)";
          bola.style.transform = "rotate(" + (360 * 7) + "deg)";
        });
      });
      disco.addEventListener("transitionend", function () { revelar(bloco); }, { once: true });
      setTimeout(function () { revelar(bloco); }, 5000);
    }
  }

  /* ---- Caça-níquel: os rolos rodam e param da esquerda para a direita ---- */
  var maquina = document.querySelector("[data-caca-niquel]");
  if (maquina) {
    var simbolos = JSON.parse(document.getElementById("simbolos-rolo").textContent);
    var rolos = Array.prototype.slice.call(maquina.querySelectorAll(".rolo"));
    var blocoMaquina = maquina.closest(".resultado");
    if (reduzir) {
      revelar(blocoMaquina);
    } else {
      var pendentes = rolos.length;
      rolos.forEach(function (rolo, i) {
        var final = rolo.dataset.final;
        var fim = Date.now() + 1300 + i * 750;
        rolo.classList.add("girando");
        var temporizador = setInterval(function () {
          if (Date.now() >= fim) {
            clearInterval(temporizador);
            rolo.textContent = final;
            rolo.classList.remove("girando");
            rolo.classList.add("parou");
            if (--pendentes === 0) revelar(blocoMaquina);
            return;
          }
          rolo.textContent = aleatorio(simbolos);
        }, 70);
      });
    }
  }

  /* ---- Dado: rola trocando de face e pousa na sorteada ---- */
  var dado = document.querySelector("[data-dado]");
  if (dado) {
    var faceFinal = parseInt(dado.dataset.dado, 10);
    var blocoDado = dado.closest(".resultado");
    function mostrarFace(n) {
      dado.className = dado.className.replace(/\bface-\d\b/, "face-" + n);
    }
    if (reduzir) {
      revelar(blocoDado);
    } else {
      dado.classList.add("rolando");
      var fimDado = Date.now() + 1500;
      var rolagem = setInterval(function () {
        if (Date.now() >= fimDado) {
          clearInterval(rolagem);
          mostrarFace(faceFinal);
          dado.classList.remove("rolando");
          dado.classList.add("parou");
          revelar(blocoDado);
          return;
        }
        mostrarFace(1 + Math.floor(Math.random() * 6));
      }, 90);
    }
  }

  /* ---- Bicho: cada prêmio cai dígito a dígito, do 1º ao 5º ---- */
  var poste = document.querySelector("[data-animar-sorteio]");
  if (poste) {
    var premios = Array.prototype.slice.call(poste.querySelectorAll(".premio"));
    poste.scrollIntoView({ behavior: reduzir ? "auto" : "smooth", block: "center" });
    if (reduzir) {
      premios.forEach(function (li) { li.classList.add("revelado"); });
      revelar(poste);
    } else {
      premios.forEach(function (li, i) {
        var digitos = Array.prototype.slice.call(li.querySelectorAll(".digito"));
        setTimeout(function () {
          li.classList.add("girando");
          digitos.forEach(function (digito, j) {
            var final = digito.dataset.final;
            var fimDigito = Date.now() + 650 + j * 260;
            var giro = setInterval(function () {
              if (Date.now() >= fimDigito) {
                clearInterval(giro);
                digito.textContent = final;
                digito.classList.add("fixo");
                if (j === digitos.length - 1) {
                  li.classList.remove("girando");
                  li.classList.add("revelado");
                  if (i === premios.length - 1) revelar(poste);
                }
                return;
              }
              digito.textContent = Math.floor(Math.random() * 10);
            }, 60);
          });
        }, 400 + i * 1200);
      });
    }
  }
})();
