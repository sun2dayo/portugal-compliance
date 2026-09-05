/**
 * Copyright (c) 2026, NovaDX - Octávio Daio and contributors
 * For license information, please see license.txt
 *
 * Sobre o Módulo - página de apresentação do Portugal Compliance:
 * os 5 Pilares de Certificação, o que o módulo cobre tecnicamente,
 * e os créditos ao autor/publisher (NovaDX). Complementa a Central
 * de Ajuda (que ensina "como usar") com uma visão de "o que é isto
 * e quem o construiu".
 */

frappe.pages['portugal-compliance-about'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Sobre o Módulo'),
		single_column: true,
	});

	new PortugalComplianceAbout(page);
};

const PCA_PILLARS = [
	{
		icon: '🔒',
		title: 'Segurança e Inviolabilidade',
		law: 'Portaria n.º 363/2010',
		text: 'Um documento fiscal assinado não pode ser alterado nem eliminado por nenhuma via - Desk, API ou acesso direto à base de dados. Toda a impressão, emissão e anulação fica registada em auditoria.',
	},
	{
		icon: '🔐',
		title: 'Criptografia e ATCUD',
		law: 'Portaria n.º 195/2020',
		text: 'Assinatura RSA-SHA1 dedicada por documento, com encadeamento de hash à assinatura anterior da mesma série. Uma ferramenta de verificação percorre toda a cadeia e confirma a sua integridade a qualquer momento.',
	},
	{
		icon: '📱',
		title: 'Layouts Legais e QR Code',
		law: 'Portaria n.º 195/2020',
		text: 'QR Code com os campos oficiais da AT (incluindo Continente/Açores/Madeira), ATCUD e certificação impressos em todos os Print Formats do módulo - e também nos 11 Print Formats nativos do ERPNext, para que nenhuma escolha de layout resulte num documento não conforme.',
	},
	{
		icon: '📁',
		title: 'Interoperabilidade (SAF-T)',
		law: 'Portaria n.º 302/2016',
		text: 'Ficheiro SAF-T (PT) v1.04_01 validado contra o XSD oficial da AT, com geração mensal automática e envio por email ao contabilista - nunca submetido automaticamente à AT, que não disponibiliza webservice para isso.',
	},
	{
		icon: '🗂️',
		title: 'Separação de Dados',
		law: 'Âmbito legal',
		text: 'Documentos recebidos de terceiros (compras) ou de uso puramente interno (stock, contabilidade) nunca consomem ATCUD, nunca são assinados e nunca entram no SAF-T como documentos fiscais emitidos.',
	},
];

const PCA_FISCAL_DOCTYPES = [
	{ name: 'Sales Invoice', role: 'Fatura (FT) ou Nota de Crédito (NC), consoante a série usada', codes: 'FT / NC' },
	{ name: 'POS Invoice', role: 'Fatura Simplificada', codes: 'FS' },
	{ name: 'Payment Entry', role: 'Recibo - RG por omissão, ou RC em Regime de IVA de Caixa', codes: 'RG / RC' },
	{ name: 'Delivery Note', role: 'Guia de Remessa', codes: 'GR' },
];

const PCA_DATA_MODEL = [
	{ name: 'Portugal Auth Settings', type: 'Single', role: 'Configuração central: credenciais da AT, certificados, chave de assinatura, modo Sandbox/Produção, método de comunicação.' },
	{ name: 'Portugal Series Configuration', type: 'Documento', role: 'Uma série documental por empresa/tipo de documento/prefixo, com o seu estado (ativa, comunicada, finalizada).' },
	{ name: 'ATCUD Log', type: 'Auditoria', role: 'Um registo por documento assinado, com o código ATCUD, a hash de assinatura e o encadeamento à anterior.' },
	{ name: 'SAF-T Export Log', type: 'Auditoria', role: 'Um registo por exportação SAF-T, com período, estado e resultado da validação contra o XSD oficial.' },
	{ name: 'Portugal AT Communication Log', type: 'Auditoria', role: 'Um registo por comunicação em tempo real à AT (faturas e guias de transporte), com estado e possibilidade de reenvio manual.' },
	{ name: 'Portugal Document Print Log', type: 'Auditoria', role: 'Um registo por impressão/reimpressão de um documento fiscal.' },
	{ name: 'AT Tax Exemption', type: 'Referência', role: 'Tabela oficial de códigos de isenção de IVA (M01-M99).' },
];

class PortugalComplianceAbout {
	constructor(page) {
		this.page = page;
		this.build_layout();
		this.render_pillars();
		this.render_sections();
	}

	build_layout() {
		this.$container = $(`
			<div class="pca-wrapper" style="max-width: 980px; margin: 0 auto; padding: 8px 4px 60px;">

				<div class="pca-hero" style="background: linear-gradient(135deg, #046a38 0%, #d4213d 100%); border-radius: 14px; padding: 28px 32px; color: #fff; margin-bottom: 24px;">
					<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
						<div style="font-size: 1.6rem; font-weight: 700; display:flex; align-items:center; gap:10px;">
							<span>🇵🇹</span> ${__('Portugal Compliance')}
						</div>
						<span style="background:rgba(255,255,255,.18); padding:4px 12px; border-radius:20px; font-size:.8rem; font-weight:600;">v${frappe.boot.versions && frappe.boot.versions.portugal_compliance ? frappe.boot.versions.portugal_compliance : '1.1.0'}</span>
					</div>
					<div style="opacity: .92; margin-top: 8px; font-size: .95rem; max-width: 680px;">
						${__('Compliance com a legislação fiscal portuguesa - ATCUD, SAF-T, QR Code, assinatura digital e trilho de auditoria - integrado de forma nativa no ERPNext.')}
					</div>
					<div style="margin-top: 14px; font-size: .85rem; opacity: .85;">
						${__('Criado e mantido por')} <b>NovaDX - Octávio Daio</b>
					</div>
				</div>

				<div class="pca-pillars" style="display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; margin-bottom: 30px;"></div>

				<div class="pca-sections"></div>

				<div class="pca-credits" style="margin-top: 40px; background: var(--card-bg, #fff); border: 1px solid var(--border-color); border-radius: 12px; padding: 24px 28px;">
					<div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 14px; display:flex; align-items:center; gap:8px;">
						<span>🏢</span> ${__('Créditos')}
					</div>
					<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; font-size:.88rem;">
						<div>
							<div class="text-muted" style="font-size:.75rem; text-transform:uppercase; letter-spacing:.03em;">${__('Autor / Publisher')}</div>
							<div style="margin-top:2px;">NovaDX - Octávio Daio</div>
						</div>
						<div>
							<div class="text-muted" style="font-size:.75rem; text-transform:uppercase; letter-spacing:.03em;">${__('Contacto')}</div>
							<div style="margin-top:2px;"><a href="mailto:compliance@novadx.pt">compliance@novadx.pt</a></div>
						</div>
						<div>
							<div class="text-muted" style="font-size:.75rem; text-transform:uppercase; letter-spacing:.03em;">${__('Licença')}</div>
							<div style="margin-top:2px;">GPL-3.0</div>
						</div>
						<div>
							<div class="text-muted" style="font-size:.75rem; text-transform:uppercase; letter-spacing:.03em;">${__('Versão')}</div>
							<div style="margin-top:2px;">1.1.0</div>
						</div>
					</div>
					<div class="text-muted small" style="margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border-color);">
						${__('Módulo de terceiros, distribuído sob licença GPL-3.0, para uso no ERPNext em conformidade com a Portaria n.º 195/2020 (ATCUD/QR Code), Portaria n.º 363/2010 (inviolabilidade) e Portaria n.º 302/2016 (SAF-T).')}
					</div>
				</div>

				<div class="text-muted small" style="text-align:center; margin-top: 24px;">
					${__('Precisa de ajuda a configurar ou a usar o módulo no dia-a-dia?')}
					<a href="/desk/portugal-compliance-help">${__('Consulte a Central de Ajuda')}</a>.
				</div>
			</div>
		`).appendTo(this.page.main);
	}

	render_pillars() {
		const $wrap = this.$container.find('.pca-pillars');
		PCA_PILLARS.forEach((p) => {
			$(`
				<div style="border:1px solid var(--border-color); border-radius:10px; padding:16px; background: var(--card-bg, #fff);">
					<div style="font-size:1.4rem;">${p.icon}</div>
					<div style="font-weight:700; margin-top:6px;">${__(p.title)}</div>
					<div class="text-muted" style="font-size:.72rem; margin-top:2px;">${p.law}</div>
					<div style="font-size:.85rem; margin-top:8px; line-height:1.5;">${__(p.text)}</div>
				</div>
			`).appendTo($wrap);
		});
	}

	render_sections() {
		const sections = this.get_sections();
		const $wrap = this.$container.find('.pca-sections');

		sections.forEach((section, idx) => {
			const $section = $(`
				<div class="pca-section" style="border:1px solid var(--border-color); border-radius:10px; margin-bottom:10px; overflow:hidden;">
					<div class="pca-section-header" style="padding:14px 18px; cursor:pointer; display:flex; align-items:center; justify-content:space-between; background: var(--subtle-fg, #fafafa);">
						<div style="font-weight:600; display:flex; align-items:center; gap:10px;">
							<span>${section.icon}</span> ${__(section.title)}
						</div>
						<span class="pca-caret transition" style="transition: transform .15s;">▸</span>
					</div>
					<div class="pca-section-body" style="display:none; padding:16px 18px; border-top:1px solid var(--border-color); font-size:.88rem; line-height:1.6;">
						${section.body}
					</div>
				</div>
			`).appendTo($wrap);

			$section.find('.pca-section-header').on('click', () => {
				const $body = $section.find('.pca-section-body');
				const $caret = $section.find('.pca-caret');
				$body.slideToggle(120);
				$caret.css('transform', $body.is(':visible') ? 'rotate(90deg)' : 'rotate(0deg)');
			});

			if (idx === 0) {
				$section.find('.pca-section-header').trigger('click');
			}
		});
	}

	get_sections() {
		const fiscal_rows = PCA_FISCAL_DOCTYPES.map((d) => `
			<tr>
				<td><a href="/app/${frappe.router.slug(d.name)}">${d.name}</a></td>
				<td>${__(d.role)}</td>
				<td><code>${d.codes}</code></td>
			</tr>
		`).join('');

		const model_rows = PCA_DATA_MODEL.map((d) => `
			<tr>
				<td><a href="/app/${frappe.router.slug(d.name)}">${d.name}</a></td>
				<td>${d.type}</td>
				<td>${__(d.role)}</td>
			</tr>
		`).join('');

		return [
			{
				icon: '🧾',
				title: 'Documentos Fiscais Suportados',
				body: `
					<p>${__('Estes são os 4 documentos que o ERPNext emite a clientes e que a lei portuguesa obriga a assinar digitalmente e a identificar com ATCUD:')}</p>
					<div style="overflow-x:auto;">
					<table class="table table-bordered" style="font-size:.85rem;">
						<thead><tr><th>${__('DocType')}</th><th>${__('Papel fiscal')}</th><th>${__('Código(s) AT')}</th></tr></thead>
						<tbody>${fiscal_rows}</tbody>
					</table>
					</div>
					<p class="text-muted" style="margin-top:8px;">${__('Faturas de compra, movimentos de stock e lançamentos contabilísticos ficam deliberadamente de fora - a responsabilidade fiscal desses documentos é de quem os emitiu, não do ERPNext.')}</p>
				`,
			},
			{
				icon: '📡',
				title: 'Comunicação em Tempo Real com a AT',
				body: `
					<p>${__('Sales Invoice, POS Invoice e Delivery Note comunicam individualmente à AT assim que são submetidos (registo de fatura ou de guia de transporte). Cada tentativa fica registada em')} <a href="/app/portugal-at-communication-log">Portugal AT Communication Log</a>, ${__('com reenvio automático periódico e um botão de reenvio manual quando falha.')}</p>
					<p>${__('As séries documentais em si (incluindo Orçamento e Nota de Encomenda, que não comunicam documento a documento) são comunicadas à AT através de um webservice próprio, separado - ver a Central de Ajuda para a distinção entre "Série Comunicada" e "Comunicado à AT".')}</p>
				`,
			},
			{
				icon: '📁',
				title: 'SAF-T (PT) Automático',
				body: `
					<p>${__('Exportação no formato oficial SAF-T (PT) v1.04_01, validada contra o XSD da Autoridade Tributária antes de ser aceite como concluída. A geração mensal corre automaticamente (dia configurável) e o ficheiro pode ser enviado por email ao contabilista.')}</p>
					<p class="text-muted">${__('O ficheiro nunca é submetido automaticamente à AT - essa via não existe como webservice oficial; a entrega continua a ser manual/por email, tal como acontece hoje fora do ERPNext.')}</p>
				`,
			},
			{
				icon: '📱',
				title: 'QR Code e Layouts Legais',
				body: `
					<p>${__('Todos os Print Formats do módulo - e também os 11 Print Formats nativos do ERPNext para os mesmos documentos fiscais (ex. "Sales Invoice Standard", "Delivery Note with Item Image") - incluem QR Code, ATCUD e o texto de certificação do software. Assim, seja qual for o layout escolhido no diálogo de impressão, o documento sai sempre em conformidade.')}</p>
					<p>${__('Quando aplicável, os layouts mostram também o motivo de isenção de IVA (M01-M07), a referência à fatura original numa Nota de Crédito, e os dados de transporte numa Guia de Remessa.')}</p>
				`,
			},
			{
				icon: '🔑',
				title: 'Arquitetura de Segurança',
				body: `
					<p>${__('Cada ambiente (Testes/Produção) tem os seus próprios certificados e chave de assinatura, guardados em localizações fixas do servidor')} (<code>/etc/portugal_compliance/certificates/</code>) ${__('e não na pasta pessoal de um utilizador - importante num sistema onde várias empresas podem partilhar o mesmo servidor.')}</p>
					<p>${__('Depois de um documento ser assinado, os seus campos fiscais (cliente, total, data, série) ficam bloqueados a alterações, e o próprio documento não pode ser eliminado.')}</p>
				`,
			},
			{
				icon: '🗄️',
				title: 'Modelo de Dados do Módulo',
				body: `
					<div style="overflow-x:auto;">
					<table class="table table-bordered" style="font-size:.85rem;">
						<thead><tr><th>${__('DocType')}</th><th>${__('Tipo')}</th><th>${__('Papel')}</th></tr></thead>
						<tbody>${model_rows}</tbody>
					</table>
					</div>
				`,
			},
		];
	}
}
