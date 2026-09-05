/**
 * Copyright (c) 2026, NovaDX - Octávio Daio and contributors
 * For license information, please see license.txt
 *
 * Liga portugal_compliance.dashboards.company.get_company_dashboard_data
 * (CompanyDashboard) a uma interface real - a classe já existia,
 * completa e testada, mas nunca tinha sido chamada de lado nenhum
 * (ver Auditoria Comparativa, Secção C: bug de "módulo sombra").
 */

frappe.pages['compliance-dashboard'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Dashboard AT'),
		single_column: true,
	});

	new PortugalComplianceDashboard(page);
};

class PortugalComplianceDashboard {
	constructor(page) {
		this.page = page;
		this.company = frappe.defaults.get_user_default('Company');

		this.setup_company_selector();
		this.build_layout();
		this.refresh();
	}

	setup_company_selector() {
		this.company_field = this.page.add_field({
			fieldtype: 'Link',
			fieldname: 'company',
			options: 'Company',
			label: __('Empresa'),
			default: this.company,
			get_query: () => ({ filters: { portugal_compliance_enabled: 1 } }),
			change: () => {
				const value = this.company_field.get_value();
				if (value && value !== this.company) {
					this.company = value;
					this.refresh();
				}
			},
		});

		this.page.set_secondary_action(__('Atualizar'), () => this.refresh(), 'refresh');
	}

	build_layout() {
		this.$container = $(`
			<div class="compliance-dashboard-wrapper" style="padding: 4px 2px 30px;">
				<div class="cd-status-banner"></div>
				<div class="cd-alerts"></div>
				<div class="cd-stats" style="display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin:18px 0;"></div>
				<div style="margin-bottom:18px;">
					<h5>${__('ATCUD gerados - últimos 6 meses')}</h5>
					<div class="cd-trend-chart"></div>
				</div>
				<div>
					<h5>${__('Séries por tipo de documento')}</h5>
					<div class="cd-series-summary"></div>
				</div>
			</div>
		`).appendTo(this.page.main);
	}

	refresh() {
		if (!this.company) {
			this.$container.find('.cd-status-banner').html(
				`<div class="alert alert-warning">${__('Selecione uma empresa com Portugal Compliance ativo.')}</div>`
			);
			return;
		}

		frappe.call({
			method: 'portugal_compliance.dashboards.company.get_company_dashboard_data',
			args: { company: this.company },
			freeze: true,
			freeze_message: __('A carregar...'),
			callback: (r) => {
				if (!r.message || r.message.error) {
					this.$container.find('.cd-status-banner').html(
						`<div class="alert alert-danger">${frappe.utils.escape_html(
							(r.message && r.message.error) || __('Erro ao carregar dashboard')
						)}</div>`
					);
					return;
				}
				this.render(r.message);
			},
		});
	}

	render(data) {
		this.render_status(data.compliance_status);
		this.render_alerts(data.alerts || []);
		this.render_stats(data.statistics || {});
		this.render_trend_chart(data.monthly_trends || []);
		this.render_series_summary(data.series_summary || {});
	}

	render_status(status) {
		if (!status) return;
		this.$container.find('.cd-status-banner').html(`
			<div class="alert alert-${this.color_to_bootstrap(status.color)}" style="margin-bottom:16px;">
				<b>${frappe.utils.escape_html(status.message || '')}</b>
			</div>
		`);
	}

	render_alerts(alerts) {
		const $wrap = this.$container.find('.cd-alerts').empty();
		if (!alerts.length) return;

		alerts.forEach((alert) => {
			const severity_color = alert.severity === 'critical' ? 'danger' : 'warning';
			$(`
				<div class="alert alert-${severity_color}" style="display:flex; justify-content:space-between; align-items:center;">
					<span>${frappe.utils.escape_html(alert.message)}</span>
					<span class="text-muted small">${frappe.utils.escape_html(alert.action || '')}</span>
				</div>
			`).appendTo($wrap);
		});
	}

	render_stats(stats) {
		const cards = [
			[__('Séries Ativas'), stats.active_series],
			[__('Séries Comunicadas'), `${stats.communicated_series || 0} / ${stats.total_series || 0}`],
			[__('% Comunicação'), `${stats.communication_percentage || 0}%`],
			[__('ATCUD Gerados (total)'), stats.total_atcud_generated],
			[__('ATCUD Este Mês'), stats.atcud_this_month],
			[__('Documentos Este Mês'), stats.documents_this_month],
		];

		const $wrap = this.$container.find('.cd-stats').empty();
		cards.forEach(([label, value]) => {
			$(`
				<div style="border:1px solid var(--border-color); border-radius:8px; padding:14px 16px; background:var(--card-bg);">
					<div style="font-size:1.4rem; font-weight:600; font-variant-numeric:tabular-nums;">${value != null ? value : '-'}</div>
					<div class="text-muted small">${frappe.utils.escape_html(label)}</div>
				</div>
			`).appendTo($wrap);
		});
	}

	render_trend_chart(trends) {
		const $wrap = this.$container.find('.cd-trend-chart').empty();
		if (!trends.length) {
			$wrap.html(`<p class="text-muted">${__('Sem dados suficientes.')}</p>`);
			return;
		}

		new frappe.Chart($wrap.get(0), {
			data: {
				labels: trends.map((t) => t.month),
				datasets: [{ name: __('ATCUD'), values: trends.map((t) => t.atcud_count) }],
			},
			type: 'bar',
			height: 220,
			colors: ['#1d4e6b'],
		});
	}

	render_series_summary(summary) {
		const $wrap = this.$container.find('.cd-series-summary').empty();
		const doc_types = Object.keys(summary);
		if (!doc_types.length) {
			$wrap.html(`<p class="text-muted">${__('Sem séries configuradas.')}</p>`);
			return;
		}

		// Grelha de cartões em vez de tabela (2026-09-04, pedido do
		// utilizador - "mais moderna graficamente" + responsividade):
		// uma tabela de 5 colunas nunca cabe num ecrã de telemóvel sem
		// scroll horizontal; um grid de cartões reflui sozinho (CSS
		// grid auto-fit) em qualquer largura, sem scroll nenhum.
		const $grid = $(
			'<div style="display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:12px;"></div>'
		).appendTo($wrap);

		doc_types.forEach((doc_type) => {
			const rows = summary[doc_type] || [];
			const active = rows.filter((r) => r.is_active).length;
			const communicated = rows.filter((r) => r.is_communicated).length;
			// documents_with_atcud/documents_communicated: contagem real
			// de DOCUMENTOS (nao series) por tipo - distingue ATCUD
			// "TEMP..." (serie ainda nao comunicada, placeholder local)
			// de um ATCUD com codigo de validacao real da AT. Antes desta
			// coluna nao havia forma de ver isto por tipo de documento,
			// so o total agregado nos cartoes de estatisticas acima.
			const docs_total = rows.reduce((sum, r) => sum + (r.documents_with_atcud || 0), 0);
			const docs_real = rows.reduce((sum, r) => sum + (r.documents_communicated || 0), 0);
			const doc_code = (rows[0] && rows[0].document_code) || '';
			// is_communicating (2026-09-05, reportado pelo utilizador):
			// Orçamento/Nota de Encomenda/Recibos nunca tem comunicação à
			// AT por documento (não existe webservice para isso - só o
			// registo da série, já refletido acima em "Séries
			// Comunicadas") - mostrar "0/3 Comunicados à AT" nestes
			// cartões sugeria uma falha que nunca poderá ser corrigida.
			// O ciclo visível destes tipos termina em "Documentos c/
			// ATCUD"; só Fatura/Fatura Simplificada/Nota de Crédito/Guia
			// de Remessa (as que realmente falam com um webservice por
			// documento) mostram esta linha.
			const is_communicating = !!(rows[0] && rows[0].is_communicating);

			const series_pill = this.ratio_pill(communicated, rows.length);
			const docs_pill = this.ratio_pill(docs_real, docs_total);

			$(`
				<div style="border:1px solid var(--border-color); border-radius:10px; padding:14px 16px; background:var(--card-bg);">
					<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
						<span style="font-weight:600;">${frappe.utils.escape_html(doc_type)}</span>
						${doc_code ? `<span class="indicator-pill gray" style="font-size:.7rem;">${frappe.utils.escape_html(doc_code)}</span>` : ''}
					</div>
					<div style="display:flex; justify-content:space-between; padding:4px 0; border-top:1px solid var(--border-color);">
						<span class="text-muted small">${__('Séries Ativas')}</span>
						<span style="font-variant-numeric:tabular-nums;">${active}</span>
					</div>
					<div style="display:flex; justify-content:space-between; align-items:center; padding:4px 0; border-top:1px solid var(--border-color);">
						<span class="text-muted small">${__('Séries Comunicadas')}</span>
						${series_pill}
					</div>
					<div style="display:flex; justify-content:space-between; padding:4px 0; border-top:1px solid var(--border-color);">
						<span class="text-muted small">${__('Documentos c/ ATCUD')}</span>
						<span style="font-variant-numeric:tabular-nums;">${docs_total}</span>
					</div>
					${is_communicating ? `
					<div style="display:flex; justify-content:space-between; align-items:center; padding:4px 0; border-top:1px solid var(--border-color);">
						<span class="text-muted small">${__('Comunicados à AT')}</span>
						${docs_pill}
					</div>
					` : ''}
				</div>
			`).appendTo($grid);
		});
	}

	ratio_pill(done, total) {
		let color = 'gray';
		if (total > 0) {
			color = done >= total ? 'green' : (done > 0 ? 'orange' : 'red');
		}
		return `<span class="indicator-pill ${color}" style="font-variant-numeric:tabular-nums;">${done} / ${total}</span>`;
	}

	color_to_bootstrap(color) {
		const map = { green: 'success', orange: 'warning', red: 'danger', gray: 'secondary' };
		return map[color] || 'secondary';
	}
}
