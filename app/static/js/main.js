const modal = document.getElementById("modalCheckpoint");
const btn = document.getElementById("abrirModal");

btn.addEventListener("click", () => {
    modal.style.display = "block";
});

window.addEventListener("click", (e) => {
    if (e.target === modal) {
        modal.style.display = "none";
    }
});

// NOVO: Modal de encerramento
const modalEncerramento = document.createElement('div');
modalEncerramento.id = "modalEncerramento";
modalEncerramento.className = "modal";
modalEncerramento.innerHTML = `
    <div class="modal-content">
        <h3>Encerrar ciclo</h3>
        <form id="formEncerramento">
            <input type="hidden" id="checkpoint_id" name="checkpoint_id">
            
            <label>Tipo</label>
            <input type="text" id="exibe_tipo" readonly disabled>
            
            <label>Data de início</label>
            <input type="text" id="exibe_data_inicio" readonly disabled>
            
            <label>Menu</label>
            <textarea id="exibe_menu" readonly disabled rows="2"></textarea>
            
            <label>Data de encerramento</label>
            <input type="text" id="exibe_data_fim" value="${new Date().toLocaleString()}" readonly disabled>
            
            <br><br>
            <button type="button" onclick="confirmarEncerramento()">✅ Confirmar encerramento</button>
            <button type="button" onclick="fecharModalEncerramento()">❌ Cancelar</button>
        </form>
    </div>
`;
document.body.appendChild(modalEncerramento);

// Função para abrir modal de encerramento
function abrirModalEncerramento(cardElement) {
    // Só permite encerrar se estiver ativo
    if (cardElement.dataset.status === 'encerrado') {
        alert('Este ciclo já foi encerrado!');
        return;
    }
    
    // Preenche o modal com os dados do card
    document.getElementById('checkpoint_id').value = cardElement.dataset.id;
    document.getElementById('exibe_tipo').value = cardElement.dataset.tipo;
    
    // Formata a data de início
    const dataInicio = new Date(cardElement.dataset.dataInicio + 'T00:00:00');
    document.getElementById('exibe_data_inicio').value = dataInicio.toLocaleString();
    
    document.getElementById('exibe_menu').value = cardElement.dataset.menu;
    
    // Abre o modal
    modalEncerramento.style.display = "block";
}

// Função para confirmar encerramento
async function confirmarEncerramento() {
    const checkpointId = document.getElementById('checkpoint_id').value;
    
    try {
        const response = await fetch(`/encerrar-checkpoint/${checkpointId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            alert('Ciclo encerrado com sucesso!');
            window.location.reload(); // Recarrega para mostrar atualizado
        } else {
            alert('Erro ao encerrar ciclo');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão');
    }
}

// Fechar modal
function fecharModalEncerramento() {
    modalEncerramento.style.display = "none";
}

// Adicionar evento de clique fora do modal
window.addEventListener("click", (e) => {
    if (e.target === modalEncerramento) {
        modalEncerramento.style.display = "none";
    }
});
