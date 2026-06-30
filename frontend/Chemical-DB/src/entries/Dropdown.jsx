import { apiFetch } from '../shared/apiFetch.js';
import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect } from 'react';
import { Dropdown } from 'react-bootstrap';




{/* <Dropdown>
<button class="btn btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
    Select company
  </button>
  <ul class="dropdown-menu">
    {companies.map( (company) => 
    <li><a class="dropdown-item" href="#">{company.name}</a></li>
    )}
  </ul>
</Dropdown> */}

<div className="form-group">
<label>Transaction Type</label>
<select className="form-control" value={transactionType} onChange={e => setTransactionType(e.target.value)}>
  <option value="Supply">Supply</option>
  <option value="Purchase">Purchase</option>
</select>
</div>