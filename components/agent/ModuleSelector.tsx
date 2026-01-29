import React from 'react';

export const AVAILABLE_MODULES = [
  { value: 'accounts', label: 'Accounts' },
  { value: 'leads', label: 'Leads' },
  { value: 'contacts', label: 'Contacts' },
  { value: 'deals', label: 'Deals' },
  { value: 'tasks', label: 'Tasks' },
  { value: 'events', label: 'Events' },
  { value: 'calls', label: 'Calls' },
  { value: 'products', label: 'Products' },
  { value: 'quotes', label: 'Quotes' },
  { value: 'sales_orders', label: 'Sales Orders' },
  { value: 'invoices', label: 'Invoices' },
  { value: 'campaigns', label: 'Campaigns' },
  { value: 'vendors', label: 'Vendors' },
  { value: 'price_books', label: 'Price Books' },
  { value: 'cases', label: 'Cases' },
  { value: 'forecasts', label: 'Forecasts' },
  { value: 'users', label: 'Users' },
  { value: 'households', label: 'Households' },
  { value: 'client_to_client_reln_new', label: 'Client Relationships' },
  { value: 'professional_contacts_new', label: 'Professional Contacts' },
  { value: 'life_events_new', label: 'Life Events' },
  { value: 'financial_goals_new', label: 'Financial Goals' },
  { value: 'income_profile_new', label: 'Income Profile' },
  { value: 'expense_profile_new', label: 'Expense Profile' },
  { value: 'asset_ownership_new', label: 'Asset Ownership' },
  { value: 'loans_new', label: 'Loans' },
  { value: 'investment_portfolios', label: 'Investment Portfolios' },
];

interface ModuleSelectorProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function ModuleSelector({ value, onChange, className }: ModuleSelectorProps) {
  return (
    <div className={`relative ${className || ''}`}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-primary focus:outline-none focus:ring-primary sm:text-sm bg-white border"
      >
        {AVAILABLE_MODULES.map((module) => (
          <option key={module.value} value={module.value}>
            {module.label}
          </option>
        ))}
      </select>
    </div>
  );
}
