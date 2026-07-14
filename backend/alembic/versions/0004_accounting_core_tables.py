"""Create accounting core tables (Phase 2)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-29
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'account_type',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('nature', sa.String(10), nullable=False),
        sa.Column('financial_statement', sa.String(30)),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('is_system', sa.Boolean(), default=False),
    )

    op.create_table(
        'financial_classification',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(30), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('display_order', sa.Integer(), default=0),
    )

    op.create_table(
        'tax_classification',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(30), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
    )

    op.create_table(
        'ifrs_classification',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(30), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('ifrs_standard', sa.String(20)),
    )

    op.create_table(
        'company_account_structure',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('digit_length', sa.Integer(), nullable=False),
        sa.Column('separator', sa.String(5), default='-'),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
    )
    op.create_unique_constraint('uq_cas_company_level', 'company_account_structure', ['company_id', 'level'])

    op.create_table(
        'account',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('parent_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('account_type_id', sa.Uuid(), sa.ForeignKey('account_type.id'), nullable=False),
        sa.Column('accepts_entries', sa.Boolean(), default=False),
        sa.Column('is_control_account', sa.Boolean(), default=False),
        sa.Column('is_auxiliary', sa.Boolean(), default=False),
        sa.Column('currency_id', sa.Uuid(), sa.ForeignKey('moneda.id')),
        sa.Column('requires_cost_center', sa.Boolean(), default=False),
        sa.Column('requires_dimension_2', sa.Boolean(), default=False),
        sa.Column('requires_dimension_3', sa.Boolean(), default=False),
        sa.Column('financial_classification_id', sa.Uuid(), sa.ForeignKey('financial_classification.id')),
        sa.Column('tax_classification_id', sa.Uuid(), sa.ForeignKey('tax_classification.id')),
        sa.Column('ifrs_classification_id', sa.Uuid(), sa.ForeignKey('ifrs_classification.id')),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('valid_from', sa.Date()),
        sa.Column('valid_to', sa.Date()),
        sa.Column('observations', sa.Text()),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('updated_by', sa.Uuid(), sa.ForeignKey('usuario.id')),
    )
    op.create_unique_constraint('uq_account_company_code', 'account', ['company_id', 'code'])
    op.create_unique_constraint('uq_account_company_parent_name', 'account', ['company_id', 'parent_id', 'name'])
    op.create_index('idx_account_company_id', 'account', ['company_id'])
    op.create_index('idx_account_parent_id', 'account', ['parent_id'])
    op.create_index('idx_account_type_id', 'account', ['account_type_id'])
    op.create_index('idx_account_active', 'account', ['company_id', 'is_active'])

    op.create_table(
        'journal_type',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('module', sa.String(50)),
        sa.Column('nature', sa.String(20), nullable=False),
        sa.Column('affects_inventory', sa.Boolean(), default=False),
        sa.Column('affects_receivable', sa.Boolean(), default=False),
        sa.Column('affects_payable', sa.Boolean(), default=False),
        sa.Column('affects_cash', sa.Boolean(), default=False),
        sa.Column('affects_bank', sa.Boolean(), default=False),
        sa.Column('requires_approval', sa.Boolean(), default=False),
        sa.Column('approval_max_amount', sa.Numeric(14, 2)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_unique_constraint('uq_jt_company_code', 'journal_type', ['company_id', 'code'])
    op.create_index('idx_jt_company', 'journal_type', ['company_id'])

    op.create_table(
        'journal_template',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('journal_type_id', sa.Uuid(), sa.ForeignKey('journal_type.id'), nullable=False),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('priority', sa.Integer(), default=0),
        sa.Column('condition_expr', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
    )
    op.create_unique_constraint('uq_jtpl_type_company_name', 'journal_template', ['journal_type_id', 'company_id', 'name'])
    op.create_index('idx_jtpl_journal', 'journal_template', ['journal_type_id'])

    op.create_table(
        'journal_template_line',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('template_id', sa.Uuid(), sa.ForeignKey('journal_template.id'), nullable=False),
        sa.Column('line_order', sa.Integer(), nullable=False),
        sa.Column('nature', sa.String(10), nullable=False),
        sa.Column('account_source', sa.String(50), nullable=False),
        sa.Column('account_code', sa.String(50)),
        sa.Column('account_param_concept', sa.String(100)),
        sa.Column('account_context_var', sa.String(100)),
        sa.Column('amount_expression', sa.Text(), nullable=False),
        sa.Column('description_expression', sa.Text()),
        sa.Column('cost_center_source', sa.String(50), default='SUBTYPE'),
        sa.Column('cost_center_id', sa.Uuid(), sa.ForeignKey('centro_costo.id')),
        sa.Column('cost_center_context_var', sa.String(100)),
        sa.Column('condition_expr', sa.Text()),
        sa.Column('is_mandatory', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
    )
    op.create_index('idx_jtt_template', 'journal_template_line', ['template_id'])

    op.create_table(
        'module_accounting_config',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('concept_code', sa.String(100), nullable=False),
        sa.Column('concept_name', sa.String(200), nullable=False),
        sa.Column('account_id', sa.Uuid(), sa.ForeignKey('account.id'), nullable=False),
        sa.Column('auxiliary_account_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cost_center_id', sa.Uuid(), sa.ForeignKey('centro_costo.id')),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('description', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('updated_by', sa.Uuid(), sa.ForeignKey('usuario.id')),
    )
    op.create_unique_constraint('uq_mac_company_module_concept', 'module_accounting_config', ['company_id', 'module', 'concept_code'])
    op.create_index('idx_mac_module', 'module_accounting_config', ['company_id', 'module'])

    op.create_table(
        'cxc_document_subtype',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('short_name', sa.String(20)),
        sa.Column('serie', sa.String(10)),
        sa.Column('uses_numeracion', sa.Boolean(), default=True),
        sa.Column('numeracion_id', sa.Uuid(), sa.ForeignKey('numeracion.id', ondelete='SET NULL')),
        sa.Column('afecta_saldo', sa.Boolean(), default=True),
        sa.Column('permite_saldo_negativo', sa.Boolean(), default=False),
        sa.Column('genera_asiento', sa.Boolean(), default=True),
        sa.Column('journal_type_id', sa.Uuid(), sa.ForeignKey('journal_type.id')),
        sa.Column('journal_template_id', sa.Uuid(), sa.ForeignKey('journal_template.id')),
        sa.Column('cuenta_principal_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_impuestos_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_descuentos_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_intereses_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_mora_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_puente_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cost_center_default_id', sa.Uuid(), sa.ForeignKey('centro_costo.id')),
        sa.Column('requiere_aprobacion', sa.Boolean(), default=False),
        sa.Column('permite_reversion', sa.Boolean(), default=True),
        sa.Column('max_dias_reversion', sa.Integer()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('observations', sa.Text()),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('updated_by', sa.Uuid(), sa.ForeignKey('usuario.id')),
    )
    op.create_unique_constraint('uq_cxc_subtype_company_code', 'cxc_document_subtype', ['company_id', 'code'])

    op.create_table(
        'cxp_document_subtype',
        sa.Column('id', sa.Uuid(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_id', sa.Uuid(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('short_name', sa.String(20)),
        sa.Column('serie', sa.String(10)),
        sa.Column('uses_numeracion', sa.Boolean(), default=True),
        sa.Column('numeracion_id', sa.Uuid(), sa.ForeignKey('numeracion.id', ondelete='SET NULL')),
        sa.Column('afecta_saldo', sa.Boolean(), default=True),
        sa.Column('permite_saldo_negativo', sa.Boolean(), default=False),
        sa.Column('genera_asiento', sa.Boolean(), default=True),
        sa.Column('journal_type_id', sa.Uuid(), sa.ForeignKey('journal_type.id')),
        sa.Column('journal_template_id', sa.Uuid(), sa.ForeignKey('journal_template.id')),
        sa.Column('cuenta_principal_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_impuestos_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_descuentos_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_retencion_iva_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_retencion_ir_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cuenta_puente_id', sa.Uuid(), sa.ForeignKey('account.id')),
        sa.Column('cost_center_default_id', sa.Uuid(), sa.ForeignKey('centro_costo.id')),
        sa.Column('requiere_aprobacion', sa.Boolean(), default=False),
        sa.Column('permite_reversion', sa.Boolean(), default=True),
        sa.Column('max_dias_reversion', sa.Integer()),
        sa.Column('afecta_inventario', sa.Boolean(), default=False),
        sa.Column('afecta_costo_promedio', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('observations', sa.Text()),
        sa.Column('created_at', sa.DateTime(), default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('updated_by', sa.Uuid(), sa.ForeignKey('usuario.id')),
    )
    op.create_unique_constraint('uq_cxp_subtype_company_code', 'cxp_document_subtype', ['company_id', 'code'])


def downgrade() -> None:
    op.drop_table('cxp_document_subtype')
    op.drop_table('cxc_document_subtype')
    op.drop_table('module_accounting_config')
    op.drop_table('journal_template_line')
    op.drop_table('journal_template')
    op.drop_table('journal_type')
    op.drop_table('account')
    op.drop_table('company_account_structure')
    op.drop_table('ifrs_classification')
    op.drop_table('tax_classification')
    op.drop_table('financial_classification')
    op.drop_table('account_type')
