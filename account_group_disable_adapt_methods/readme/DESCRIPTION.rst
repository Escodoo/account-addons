This module disables the execution of the adapt methods that are executed in the write and create methods of the account.group model. This is justified in cases of mass update of account.group since the execution of these methods makes the process very time-consuming.

.. code-block:: python

    # Original Methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'code_prefix_start' in vals and not vals.get('code_prefix_end'):
                vals['code_prefix_end'] = vals['code_prefix_start']
        res_ids = super(AccountGroup, self).create(vals_list)
        res_ids._adapt_accounts_for_account_groups()
        res_ids._adapt_parent_account_group()
        return res_ids

    def write(self, vals):
        res = super(AccountGroup, self).write(vals)
        if 'code_prefix_start' in vals or 'code_prefix_end' in vals:
            self._adapt_accounts_for_account_groups()
            self._adapt_parent_account_group()
        return res


    # New Methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'code_prefix_start' in vals and not vals.get('code_prefix_end'):
                vals['code_prefix_end'] = vals['code_prefix_start']
        return super(AccountGroupInherit, self).create(vals_list)

    def write(self, vals):
        return super(AccountGroupInherit, self).write(vals)

In addition, an action is implemented to execute the adapt methods by account group or groups.
