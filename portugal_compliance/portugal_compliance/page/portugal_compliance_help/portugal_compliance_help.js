/**
 * Copyright (c) 2026, NovaDX - Octávio Daio and contributors
 * For license information, please see license.txt
 *
 * Central de Ajuda do Portugal Compliance - guia passo-a-passo,
 * atalhos diretos para as zonas de configuração/consulta mais usadas
 * e um FAQ com dúvidas reais encontradas durante o desenvolvimento e
 * testes ao vivo deste módulo (não just uma cópia do manual técnico -
 * escrito de propósito em linguagem simples, sem jargão de código).
 */

frappe.pages['portugal-compliance-help'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Central de Ajuda'),
		single_column: true,
	});

	new PortugalComplianceHelp(page);
};

const PT_HELP_QUICK_LINKS = [
	{ icon: '⚙️', label: 'Portugal Auth Settings', desc: 'Credenciais, certificados e modo Sandbox/Produção', href: '/desk/portugal-auth-settings' },
	{ icon: '#️⃣', label: 'Séries Portuguesas', desc: 'Criar, comunicar, finalizar ou anular séries', href: '/desk/portugal-series-configuration' },
	{ icon: '📊', label: 'Dashboard AT', desc: 'Visão geral do estado de compliance da empresa', href: '/desk/compliance-dashboard' },
	{ icon: '🏢', label: 'Empresa (Company)', desc: 'NIF, morada e ativação do Compliance', href: '/desk/company' },
	{ icon: '🔐', label: 'ATCUD Log', desc: 'Auditoria de cada código único gerado', href: '/desk/atcud-log' },
	{ icon: '📁', label: 'SAF-T Export Log', desc: 'Ficheiros SAF-T gerados e o seu estado', href: '/desk/saf-t-export-log' },
	{ icon: '📡', label: 'Comunicações AT', desc: 'Estado de cada comunicação individual à AT', href: '/desk/portugal-at-communication-log' },
	{ icon: '％', label: 'Modelos de Imposto', desc: 'Sales Taxes Template, Item Tax Template, Tax Category', href: '/desk/sales-taxes-and-charges-template' },
];

class PortugalComplianceHelp {
	constructor(page) {
		this.page = page;
		this.build_layout();
		this.render_quick_links();
		this.render_sections();
		this.render_faq();
		this.setup_search();
		this.setup_accordion();
	}

	build_layout() {
		this.$container = $(`
			<div class="pch-wrapper" style="max-width: 980px; margin: 0 auto; padding: 8px 4px 60px;">

				<div class="pch-hero" style="background: linear-gradient(135deg, #046a38 0%, #d4213d 100%); border-radius: 14px; padding: 28px 32px; color: #fff; margin-bottom: 24px;">
					<div style="font-size: 1.6rem; font-weight: 700; display:flex; align-items:center; gap:10px;">
						<span>🇵🇹</span> ${__('Central de Ajuda — Portugal Compliance')}
					</div>
					<div style="opacity: .92; margin-top: 6px; font-size: .95rem; max-width: 640px;">
						${__('Tudo o que precisa para configurar a sua empresa, emitir faturas com ATCUD e QR Code, e comunicar com a Autoridade Tributária - sem sair do ERPNext.')}
					</div>
					<div style="margin-top: 16px;">
						<input type="text" class="pch-search form-control" placeholder="${__('Pesquisar um tópico ou uma dúvida... (ex: certificado, NIF, série)')}"
							style="max-width: 480px; border: none; padding: 10px 14px; border-radius: 8px; font-size: .9rem;">
					</div>
				</div>

				<div class="pch-quick-links" style="display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:12px; margin-bottom: 30px;"></div>

				<div class="pch-search-empty text-muted" style="display:none; text-align:center; padding: 40px 0;">
					${__('Sem resultados. Tente outra palavra, ou consulte as Perguntas Frequentes mais abaixo.')}
				</div>

				<div class="pch-sections"></div>

				<div class="pch-faq-header" style="display:flex; align-items:center; gap:10px; margin: 36px 0 16px;">
					<span style="font-size:1.3rem;">💬</span>
					<span style="font-size:1.2rem; font-weight:700;">${__('Perguntas Frequentes')}</span>
				</div>
				<div class="pch-faq"></div>

				<div class="text-muted small" style="text-align:center; margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border-color);">
					${__('Não encontrou o que precisava? Os manuais técnicos completos (arquitetura, schema de dados, integração AT) estão na pasta')} <code>documentation/</code> ${__('do módulo, para a equipa técnica.')}
				</div>
			</div>
		`).appendTo(this.page.main);
	}

	// ------------------------------------------------------------------
	// Atalhos rápidos
	// ------------------------------------------------------------------
	render_quick_links() {
		const $grid = this.$container.find('.pch-quick-links');
		PT_HELP_QUICK_LINKS.forEach((item) => {
			$(`
				<a href="${item.href}" class="pch-quick-link" style="display:block; text-decoration:none; border:1px solid var(--border-color); border-radius:10px; padding:14px 16px; background:var(--card-bg); transition: box-shadow .15s, transform .15s;">
					<div style="font-size:1.4rem;">${item.icon}</div>
					<div style="font-weight:600; margin-top:4px; color: var(--text-color);">${frappe.utils.escape_html(item.label)}</div>
					<div class="text-muted small" style="margin-top:2px;">${frappe.utils.escape_html(item.desc)}</div>
				</a>
			`).appendTo($grid);
		});

		// Pequeno efeito hover (elevação) - sem depender de CSS externo.
		this.$container.on('mouseenter', '.pch-quick-link', function () {
			$(this).css({ 'box-shadow': '0 4px 12px rgba(0,0,0,.08)', transform: 'translateY(-2px)' });
		}).on('mouseleave', '.pch-quick-link', function () {
			$(this).css({ 'box-shadow': 'none', transform: 'none' });
		});
	}

	// ------------------------------------------------------------------
	// Secções principais (acordeão)
	// ------------------------------------------------------------------
	render_sections() {
		const $wrap = this.$container.find('.pch-sections');
		this.get_sections().forEach((section, idx) => {
			$(this.section_html(section, idx === 0)).appendTo($wrap);
		});
	}

	section_html(section, open_by_default) {
		return `
			<div class="pch-section" data-search-text="${frappe.utils.escape_html((section.title + ' ' + section.plain).toLowerCase())}"
				style="border:1px solid var(--border-color); border-radius:10px; margin-bottom:12px; overflow:hidden; background:var(--card-bg);">
				<div class="pch-section-header" style="display:flex; align-items:center; gap:12px; padding:14px 18px; cursor:pointer; user-select:none;">
					<span style="font-size:1.3rem;">${section.icon}</span>
					<span style="font-weight:600; flex:1;">${frappe.utils.escape_html(section.title)}</span>
					<span class="pch-chevron text-muted" style="transition: transform .15s;">▾</span>
				</div>
				<div class="pch-section-body" style="padding: 0 18px 18px; display:${open_by_default ? 'block' : 'none'};">
					${section.html}
				</div>
			</div>
		`;
	}

	callout(type, html) {
		const styles = {
			info: { bg: 'rgba(46,134,222,.08)', border: '#2e86de', icon: 'ℹ️' },
			warning: { bg: 'rgba(255,159,26,.1)', border: '#ff9f1a', icon: '⚠️' },
			success: { bg: 'rgba(39,174,96,.1)', border: '#27ae60', icon: '✅' },
			tip: { bg: 'rgba(155,89,182,.1)', border: '#9b59b6', icon: '💡' },
		}[type] || { bg: 'rgba(0,0,0,.04)', border: '#999', icon: 'ℹ️' };

		return `
			<div style="background:${styles.bg}; border-left:3px solid ${styles.border}; border-radius:6px; padding:10px 14px; margin:12px 0; font-size:.9rem;">
				<span style="margin-right:6px;">${styles.icon}</span>${html}
			</div>
		`;
	}

	link(href, label) {
		return `<a href="${href}">${frappe.utils.escape_html(label)} ↗</a>`;
	}

	get_sections() {
		return [
			// ---------------------------------------------------------
			{
				icon: '🚀',
				title: __('Antes de começar'),
				plain: 'requisitos NIF certificados credenciais webservice',
				html: `
					<p>${__('Para configurar o Portugal Compliance de ponta a ponta, tenha à mão:')}</p>
					<ul>
						<li>${__('Acesso de <b>Administrador</b> (ou perfil System Manager).')}</li>
						<li>${__('O <b>NIF</b> da empresa.')}</li>
						<li>${__('Os <b>certificados</b> fornecidos pela AT: o certificado mTLS (cliente), a sua chave privada, e o certificado público da AT. Em ambiente de testes, a AT disponibiliza um conjunto próprio de certificados de sandbox.')}</li>
						<li>${__('A <b>chave privada RSA</b> usada para assinar digitalmente os documentos (distinta dos certificados mTLS).')}</li>
						<li>${__('As <b>credenciais do webservice da AT</b> - um utilizador no formato <code>NIF/subutilizador</code> (ex. <code>518747832/1</code>) e a respetiva password. São diferentes do login normal do Portal das Finanças.')}</li>
					</ul>
					${this.callout('tip', __('O processo completo, numa empresa nova, demora tipicamente entre 15 a 30 minutos.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '1️⃣',
				title: __('Passo 1 — Criar a Empresa'),
				plain: 'empresa company nif morada address plano de contas',
				html: `
					<ol>
						<li>${__('Em')} ${this.link('/desk/company/new', __('Organization › Company'))}, ${__('crie a empresa com')} <b>${__('Chart of Accounts')} = "Portugal - Plano de Contas SNC"</b>, <b>Country = Portugal</b> ${__('e')} <b>Default Currency = EUR</b>.
						${__('Isto cria automaticamente todas as contas SNC, incluindo as subcontas de IVA.')}</li>
						<li>${__('Grave, reabra a empresa e preencha o campo <b>NIF</b> (ex. <code>518747832</code>).')}</li>
						<li>${__('Preencha a <b>Morada</b> completa da sede (Rua, Cidade, Código Postal). Este passo <b>não é opcional</b>: sem morada completa, a exportação SAF-T falha a validação (a AT rejeitaria o ficheiro).')}</li>
					</ol>
					${this.callout('warning', __('O <b>NIF</b> e o <b>País</b> ficam bloqueados para edição assim que a empresa emitir o primeiro documento fiscal - é uma proteção legal, não um erro. Veja a pergunta sobre isto no FAQ mais abaixo.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '2️⃣',
				title: __('Passo 2 — Portugal Auth Settings (credenciais e certificados)'),
				plain: 'auth settings credenciais certificados mtls sandbox producao webservice ambiente criptografia',
				html: `
					<p>${__('É aqui que vive tudo o que o sistema precisa para falar com a Autoridade Tributária. Aceda em')} ${this.link('/desk/portugal-auth-settings', 'Portugal Compliance › Portugal Auth Settings')} ${__('(é um documento único - edita-se sempre o mesmo, nunca se cria um novo).')}</p>
					<p>${__('O formulário está organizado em 4 separadores:')}</p>
					<ul>
						<li><b>${__('Ambiente')}</b> - ${__('o interruptor Sandbox/Produção, o endereço do webservice e as credenciais de utilizador da AT (formato <code>NIF/subutilizador</code>).')}</li>
						<li><b>${__('Criptografia')}</b> - ${__('a chave de assinatura RSA (a que assina digitalmente cada documento) e os 3 certificados mTLS/WS-Security.')}</li>
						<li><b>${__('Regras de Negócio')}</b> - ${__('criação automática de séries, validação de NIF, regime de IVA de caixa, impressão de documentos anulados.')}</li>
						<li><b>${__('Comunicação AT')}</b> - ${__('como e quando cada tipo de documento (faturas, guias, SAF-T mensal) é comunicado.')}</li>
					</ul>
					${this.callout('tip', __('<b>Deteção automática de certificados:</b> ao mudar o interruptor Sandbox/Produção, o sistema procura sozinho os certificados no local oficial do servidor (<code>/etc/portugal_compliance/certificates/test/</code> ou <code>/prod/</code>) e preenche os 3 campos automaticamente, se os encontrar. Se preencher um caminho manualmente, essa escolha é sempre respeitada - a deteção automática nunca substitui um valor que não tenha sido ela própria a colocar lá.'))}
					${this.callout('info', __('A chave de assinatura de documentos é independente do modo Sandbox/Produção - é a mesma em qualquer ambiente, até ser substituída pela chave definitiva após certificação do software.'))}
					<p>${__('Grave. Se os campos obrigatórios estiverem corretos, o botão')} <b>Test Connection</b> ${__('(menu Ações, no topo) confirma a ligação real ao webservice da AT.')}</p>
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '3️⃣',
				title: __('Passo 3 — Ativar o Compliance na Empresa'),
				plain: 'ativar compliance enabled series automaticas pos',
				html: `
					<ol>
						<li>${__('Abra a ficha da sua empresa e marque <b>Portugal Compliance Enabled</b>.')}</li>
						<li>${__('Grave. O sistema cria automaticamente as 5 séries base (Fatura, Fatura Simplificada, Recibo, Guia de Remessa, Nota de Crédito), já com o prefixo correto (ex. <code>FT2026NDX</code>).')}</li>
						<li>${__('O POS passa automaticamente a emitir sempre Fatura Simplificada (nunca Fatura normal), a menos que já tenha escolhido outra opção manualmente antes.')}</li>
					</ol>
					${this.callout('warning', __('Uma série criada aqui ainda <b>não tem valor fiscal</b> até ser comunicada à AT - ver Passo 4.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '4️⃣',
				title: __('Passo 4 — Comunicar as Séries à AT'),
				plain: 'comunicar series webservice at validacao codigo',
				html: `
					<p>${__('Uma série só pode ser usada para emitir documentos com valor fiscal depois de comunicada à AT - é a AT que atribui o código de validação usado em cada ATCUD.')}</p>
					<ol>
						<li>${__('Na ficha da empresa, menu <b>Comunicação AT › Comunicar Séries</b>.')}</li>
						<li>${__('Confirme - esta ação <b>não pode ser desfeita</b>, cada série comunicada fica registada na AT de forma permanente.')}</li>
						<li>${__('Confirme em')} ${this.link('/desk/portugal-series-configuration', 'Portugal Series Configuration')} ${__('que cada série passou a mostrar')} <span class="indicator-pill green" style="font-size:.75rem;">${__('Comunicada')}</span>.</li>
					</ol>
					${this.callout('tip', __('Criou uma série nova a meio do ano? Não repita a comunicação em bloco (reenviaria também as já comunicadas). Abra só essa série e use o botão <b>Comunicar à AT</b> nela.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '5️⃣',
				title: __('Passo 5 — Emitir os Primeiros Documentos'),
				plain: 'fatura sales invoice recibo payment entry pos fatura simplificada guia delivery note nota de credito atcud qr code',
				html: `
					<p>${__('Com as séries comunicadas, cada um destes documentos gera automaticamente <b>ATCUD</b> e <b>QR Code</b> ao ser submetido - nada a configurar manualmente:')}</p>
					<table class="table table-bordered" style="font-size:.88rem;">
						<thead><tr><th>${__('Documento')}</th><th>${__('Onde emitir')}</th><th>${__('Nota específica')}</th></tr></thead>
						<tbody>
							<tr><td>${__('Fatura')}</td><td>${this.link('/desk/sales-invoice/new', 'Sales Invoice')}</td><td>${__('Série e IVA já vêm pré-selecionados pela empresa ativa.')}</td></tr>
							<tr><td>${__('Recibo')}</td><td>${this.link('/desk/payment-entry/new', 'Payment Entry')}</td><td>${__('NIF do cliente obrigatório acima de €1000.')}</td></tr>
							<tr><td>${__('Fatura Simplificada')}</td><td>${this.link('/desk/point-of-sale', 'POS')}</td><td>${__('Exige POS Profile e turno de caixa (POS Opening Entry) abertos primeiro.')}</td></tr>
							<tr><td>${__('Guia de Remessa')}</td><td>${this.link('/desk/delivery-note/new', 'Delivery Note')}</td><td>${__('Exige peso do artigo e morada de entrega preenchidos - a AT recusa sem isto.')}</td></tr>
							<tr><td>${__('Nota de Crédito')}</td><td>${__('Botão "Create › Return / Credit Note" na Fatura original')}</td><td>${__('Nunca edita a fatura original; recebe ATCUD e assinatura próprios.')}</td></tr>
						</tbody>
					</table>
					${this.callout('info', __('Um documento em <b>rascunho</b> nunca tem ATCUD nem assinatura - só ao <b>Submeter</b> é que o documento se torna definitivo e imutável (Portaria 195/2020). Para corrigir um erro depois de submetido: anule o documento (se for o primeiro erro, antes do cliente o receber) ou emita uma Nota de Crédito (se o cliente já o tiver em mãos) - nunca edite valores diretamente.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '6️⃣',
				title: __('Passo 6 — Gerar a Exportação SAF-T'),
				plain: 'saft export xml mensal auditoria',
				html: `
					<ol>
						<li>${this.link('/desk/saf-t-export-log/new', 'SAF-T Export Log')} → ${__('escolha a Empresa, o tipo (Full) e o período (From/To Date).')}</li>
						<li>${__('Grave - a geração é automática, sem botão separado. Em segundos o registo mostra o estado (<code>Completed</code>/<code>Failed</code>), o ficheiro XML e a validação contra o esquema oficial da AT.')}</li>
						<li>${__('Descarregue o ficheiro diretamente na lista (botão de download) ou a partir do registo.')}</li>
					</ol>
					${this.callout('warning', __('Se o estado ficar <code>Failed</code>, a causa mais comum é a morada da empresa em falta (Passo 1). Preencha-a e crie um novo registo - não precisa repetir mais nada.'))}
					${this.callout('tip', __('Pode configurar em Portugal Auth Settings (separador Comunicação AT) a geração automática mensal, com ou sem envio por email ao contabilista. Não existe (nem a AT disponibiliza) um envio automático à AT por webservice - a submissão do SAF-T é sempre manual, por upload no Portal das Finanças.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '7️⃣',
				title: __('Passo 7 — Dashboard AT'),
				plain: 'dashboard estatisticas atcud graficos cartoes comunicados',
				html: `
					<p>${this.link('/desk/compliance-dashboard', 'Dashboard AT')} ${__('dá uma visão consolidada e em tempo real: séries ativas/comunicadas, ATCUD gerados, e um cartão por tipo de documento.')}</p>
					${this.callout('info', __('Repare que <b>nem todos os cartões mostram "Comunicados à AT"</b> - Orçamento, Nota de Encomenda e Recibos terminam em "Documentos c/ ATCUD", de propósito. Explicamos exatamente porquê no FAQ mais abaixo.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '🗂️',
				title: __('Gestão de Séries: Comunicar, Finalizar e Anular'),
				plain: 'series finalizar anular comunicar individual gestao',
				html: `
					<p>${__('A partir de')} ${this.link('/desk/portugal-series-configuration', 'Portugal Series Configuration')}, ${__('cada série tem 3 ações possíveis (menu Portugal Compliance, no topo do documento):')}</p>
					<table class="table table-bordered" style="font-size:.88rem;">
						<thead><tr><th></th><th>${__('Comunicar')}</th><th>${__('Finalizar')}</th><th>${__('Anular')}</th></tr></thead>
						<tbody>
							<tr><td><b>${__('Quando usar')}</b></td><td>${__('Série nova, ainda não comunicada')}</td><td>${__('Fim de ano fiscal ou fim de vida da série')}</td><td>${__('Só logo a seguir a uma comunicação feita por engano')}</td></tr>
							<tr><td><b>${__('Prazo')}</b></td><td>${__('A qualquer momento')}</td><td>${__('Sem limite')}</td><td>${__('Apenas no dia da comunicação ou no seguinte')}</td></tr>
							<tr><td><b>${__('Documentos já emitidos')}</b></td><td>—</td><td>${__('Qualquer quantidade, ficam válidos')}</td><td>${__('Tem de ter zero')}</td></tr>
							<tr><td><b>${__('Efeito')}</b></td><td>${__('Atribui código de validação da AT')}</td><td>${__('Fecha para novos documentos; histórico válido')}</td><td>${__('Desfaz o registo, como se nunca tivesse existido')}</td></tr>
						</tbody>
					</table>
					${this.callout('warning', __('Anular exige confirmação explícita de que a série tem zero documentos emitidos. Se já emitiu um único documento, a única via é Finalizar.'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '📡',
				title: __('Comunicação em Tempo Real e Reenvio'),
				plain: 'comunicacao tempo real webservice registerinvoice reenviar retry falhada portugal at communication log',
				html: `
					<p>${__('Com o Método de Comunicação de Faturas em "Tempo Real (Webservice)" (Passo 2), cada Fatura, Fatura Simplificada ou Guia de Remessa submetida dispara uma comunicação real à AT em segundo plano, sem atrasar a submissão.')}</p>
					<p>${__('Cada tentativa fica registada em')} ${this.link('/desk/portugal-at-communication-log', 'Portugal AT Communication Log')}, ${__('com o estado (Pendente/Sucesso/Falhou/A repetir), a resposta da AT, e a data/hora da última tentativa.')}</p>
					${this.callout('tip', __('Uma comunicação falhada tenta-se automaticamente de novo, com intervalos crescentes. Se já corrigiu a causa (ex. credencial errada) e não quer esperar, abra o registo e use o botão de reenvio imediato.'))}
					${this.callout('info', __('Só Fatura, Fatura Simplificada e Guia de Remessa passam por aqui. Orçamentos, Notas de Encomenda e Recibos nunca aparecem nesta lista - não é um erro, é porque a AT não disponibiliza nenhum canal para os comunicar individualmente (ver FAQ).'))}
				`,
			},
			// ---------------------------------------------------------
			{
				icon: '🧭',
				title: __('Resumo do fluxo completo'),
				plain: 'resumo fluxo diagrama passos',
				html: `
					<div style="display:flex; flex-direction:column; gap:6px; font-size:.9rem;">
						${[
							__('1. Criar Empresa (NIF + Morada)'),
							__('2. Configurar Portugal Auth Settings (credenciais + certificados)'),
							__('3. Ativar "Portugal Compliance Enabled" (cria séries automaticamente)'),
							__('4. Comunicar Séries à AT (obrigatório antes de emitir)'),
							__('5. Emitir Documentos (ATCUD + QR Code automáticos)'),
							__('6. Gerar Exportação SAF-T'),
							__('7. Consultar Dashboard AT para verificação global'),
						].map((step, i, arr) => `
							<div style="display:flex; align-items:center; gap:10px;">
								<span class="indicator-pill blue" style="min-width:26px; text-align:center;">${i + 1}</span>
								<span>${step.replace(/^\d+\.\s*/, '')}</span>
							</div>
							${i < arr.length - 1 ? '<div style="margin-left:12px; color:var(--text-muted);">↓</div>' : ''}
						`).join('')}
					</div>
					${this.callout('tip', __('Cada seta é uma dependência real imposta pelo próprio sistema - não é possível, por exemplo, emitir uma fatura numa série não comunicada.'))}
				`,
			},
		];
	}

	// ------------------------------------------------------------------
	// FAQ
	// ------------------------------------------------------------------
	get_faq() {
		return [
			{
				q: __('Porque é que o cartão de Orçamento / Nota de Encomenda / Recibo não mostra "Comunicados à AT"?'),
				a: __('Porque nunca poderiam mostrar um valor real: a Autoridade Tributária não disponibiliza nenhum webservice para comunicar Orçamentos, Notas de Encomenda ou Recibos individualmente - só existe comunicação por documento para Fatura, Fatura Simplificada e Guia de Remessa. Mostrar "0/3 Comunicados à AT" nesses cartões sugeria uma falha que nunca poderia ser corrigida. O ciclo visível desses tipos termina propositadamente em "Documentos c/ ATCUD".'),
			},
			{
				q: __('Qual a diferença entre "Série Comunicada" e "Comunicado à AT"?'),
				a: __('"Série Comunicada" refere-se ao registo da <b>série</b> junto da AT (o webservice de séries, que atribui o código de validação usado em todos os ATCUD dessa série) - todos os tipos de documento passam por isto. "Comunicado à AT" refere-se ao envio individual de <b>cada documento</b> (webservice de faturação) - só existe para Fatura, Fatura Simplificada e Guia de Remessa. Uma série pode estar 100% comunicada mesmo que os seus documentos nunca sejam comunicados individualmente (Orçamentos, por exemplo).'),
			},
			{
				q: __('Não consigo alterar o NIF ou o País da empresa - o campo está bloqueado. Porquê?'),
				a: __('Assim que a empresa emite o primeiro documento fiscal, o NIF e o País ficam permanentemente bloqueados - alterá-los depois corromperia a identidade fiscal de tudo o que já foi assinado e comunicado à AT (Portaria 363/2010). Se o NIF ainda estiver vazio nesse momento (por exemplo, se documentos de teste foram criados antes de o preencher), o campo continua editável uma única vez - assim que gravar um valor, fica bloqueado da mesma forma.'),
			},
			{
				q: __('Onde coloco os certificados mTLS e a chave de assinatura no servidor?'),
				a: __('Nas pastas oficiais do sistema: <code>/etc/portugal_compliance/certificates/test/</code> para sandbox e <code>/etc/portugal_compliance/certificates/prod/</code> para produção (ficheiros <code>mtls_client_cert.pem</code>, <code>mtls_client_key.pem</code> e <code>at_public_key_&lt;ano&gt;.cer</code>), e <code>/etc/portugal_compliance/signing_keys/invoice_signing_key.pem</code> para a chave de assinatura. Nunca na pasta pessoal (home) de um utilizador do sistema - num ambiente de produção o serviço web pode correr com outro utilizador e perder a permissão de leitura.'),
			},
			{
				q: __('Qual a diferença entre Anular um documento e emitir uma Nota de Crédito?'),
				a: __('Anular é para um erro imediato, detetado antes de o cliente receber o documento - o ATCUD mantém-se registado para auditoria, mas o documento fica marcado como anulado. A Nota de Crédito é para quando o cliente já tem o documento em mãos - estorna o valor, no todo ou em parte, sem tocar no documento original. Nunca use uma via para simular a outra.'),
			},
			{
				q: __('Porque é que um documento em rascunho não tem ATCUD nem assinatura?'),
				a: __('Por desenho: o ATCUD e a assinatura digital só são gerados no momento em que o documento é <b>submetido</b> (Submit), nunca antes. Isto evita "rascunhos zombie" com ATCUD atribuído que depois são editados ou apagados - o ATCUD tem de corresponder sempre a um documento definitivo e imutável.'),
			},
			{
				q: __('O que significa um código de validação a começar por "TEMP"?'),
				a: __('É um código provisório, gerado localmente, usado enquanto a série ainda não foi comunicada à AT. Assim que a série é comunicada com sucesso, os documentos seguintes já recebem o código de validação real devolvido pela AT. Documentos emitidos antes da comunicação mantêm o código TEMP - não é retroativo.'),
			},
			{
				q: __('Posso usar os mesmos certificados em Sandbox e em Produção?'),
				a: __('Não - a AT emite certificados e credenciais diferentes para cada ambiente. O sistema deteta isto automaticamente: ao mudar o interruptor Sandbox/Produção em Portugal Auth Settings, procura os certificados na pasta correspondente e atualiza os 3 campos sozinho, se os encontrar.'),
			},
			{
				q: __('A guia de transporte foi recusada com um erro sobre peso ou morada. O que fazer?'),
				a: __('A AT exige, para documentos de transporte, o peso de cada artigo (campo Weight Per Unit / Weight UOM na linha do artigo) e uma morada de entrega válida (associada ao Cliente correto). O sistema recusa gravar a guia sem estes dados, com uma mensagem explícita a indicar qual dos dois está em falta.'),
			},
			{
				q: __('Uma série nunca vai "esgotar" ao passar de 9999 documentos?'),
				a: __('Não. O padrão <code>####</code> no nome da série é só o número mínimo de zeros à esquerda - ao chegar ao documento 10.000, o sistema passa automaticamente para 5 algarismos, depois 6, e assim sucessivamente, sem qualquer intervenção manual nem quebra de validade fiscal.'),
			},
		];
	}

	render_faq() {
		const $wrap = this.$container.find('.pch-faq');
		this.get_faq().forEach((item, idx) => {
			$(`
				<div class="pch-faq-item" data-search-text="${frappe.utils.escape_html((item.q + ' ' + item.a).toLowerCase())}"
					style="border:1px solid var(--border-color); border-radius:8px; margin-bottom:8px; background:var(--card-bg);">
					<div class="pch-section-header" style="display:flex; align-items:center; gap:10px; padding:12px 16px; cursor:pointer; user-select:none;">
						<span style="font-weight:600; flex:1; font-size:.92rem;">${frappe.utils.escape_html(item.q)}</span>
						<span class="pch-chevron text-muted" style="transition: transform .15s;">▾</span>
					</div>
					<div class="pch-section-body text-muted" style="padding: 0 16px 14px; display:none; font-size:.88rem; line-height:1.5;">
						${item.a}
					</div>
				</div>
			`).appendTo($wrap);
		});
	}

	// ------------------------------------------------------------------
	// Interação: acordeão + pesquisa
	// ------------------------------------------------------------------
	setup_accordion() {
		this.$container.on('click', '.pch-section-header', function () {
			const $body = $(this).siblings('.pch-section-body');
			const $chevron = $(this).find('.pch-chevron');
			const is_open = $body.is(':visible');
			$body.slideToggle(120);
			$chevron.css('transform', is_open ? 'rotate(0deg)' : 'rotate(-180deg)');
		});
	}

	setup_search() {
		const $input = this.$container.find('.pch-search');
		const $sections = this.$container.find('.pch-section');
		const $faq_items = this.$container.find('.pch-faq-item');
		const $empty = this.$container.find('.pch-search-empty');

		$input.on('input', () => {
			const term = ($input.val() || '').toLowerCase().trim();
			let any_visible = false;

			$sections.add($faq_items).each(function () {
				const $el = $(this);
				const matches = !term || ($el.data('search-text') || '').includes(term);
				$el.toggle(matches);
				if (matches) {
					any_visible = true;
					// Ao pesquisar, abrir diretamente o resultado - o
					// utilizador não devia ter de clicar outra vez para
					// ver o que procurou.
					if (term) {
						$el.find('.pch-section-body').show();
						$el.find('.pch-chevron').css('transform', 'rotate(-180deg)');
					}
				}
			});

			this.$container.find('.pch-search-empty').toggle(term.length > 0 && !any_visible);
		});
	}
}
