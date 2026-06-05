document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const body = document.body;
    const themeToggleBtn = document.getElementById('theme-toggle');
    const healthStatusDiv = document.getElementById('health-status');
    const orderForm = document.getElementById('order-form');
    const orderTypeSelect = document.getElementById('order_type');
    const priceGroup = document.getElementById('price-group');
    const stopPriceGroup = document.getElementById('stop-price-group');
    const priceInput = document.getElementById('price');
    const stopPriceInput = document.getElementById('stop_price');
    const submitBtn = document.getElementById('submit-order-btn');
    const terminalConsole = document.getElementById('terminal-console');
    const ordersTableBody = document.querySelector('#orders-table tbody');
    const buyRadio = document.getElementById('side-buy');
    const sellRadio = document.getElementById('side-sell');
    const symbolInput = document.getElementById('symbol');
    
    // Wallet UI Elements
    const walletBalanceSpan = document.getElementById('wallet-balance');
    const walletPositionSpan = document.getElementById('wallet-position');
    const walletPositionValueSpan = document.getElementById('wallet-position-value');
    const walletTotalValueSpan = document.getElementById('wallet-total-value');
    const loadFundsBtn = document.getElementById('load-funds-btn');
    const loadAmountInput = document.getElementById('load-amount-input');
    const mockModeCheckbox = document.getElementById('mock-mode-checkbox');
    const walletModalBtn = document.getElementById('wallet-modal-btn');
    const closeWalletBtn = document.getElementById('close-wallet-btn');
    const walletModal = document.getElementById('wallet-modal');

    // Global tracking of wallet values for real-time price updates
    let currentBalance = 10000.0;
    let currentPosition = 0.0;
    let currentTotalDeposited = 10000.0;

    // Helper to format profit/loss value into premium colored badge markup
    function formatProfitLoss(plValue) {
        const absValue = Math.abs(plValue).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        if (plValue > 0) {
            return `<span class="pl-badge positive">+ $${absValue}</span>`;
        } else if (plValue < 0) {
            return `<span class="pl-badge negative">- $${absValue}</span>`;
        } else {
            return `<span class="pl-badge neutral">$0.00</span>`;
        }
    }

    // Fetch Wallet Status
    function fetchWallet() {
        const symbol = symbolInput.value.trim().toUpperCase() || 'BTCUSDT';
        fetch(`/api/wallet?symbol=${symbol}`)
            .then(res => res.json())
            .then(data => {
                currentBalance = parseFloat(data.balance || 0);
                currentPosition = parseFloat(data.position || 0);
                currentTotalDeposited = parseFloat(data.total_deposited || 10000.0);
                const positionValue = parseFloat(data.position_value || 0);
                const totalValue = parseFloat(data.total_value || 0);
                const profitLoss = parseFloat(data.profit_loss || 0);
                
                walletBalanceSpan.innerText = `$${currentBalance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                walletPositionSpan.innerText = `${currentPosition.toLocaleString(undefined, {minimumFractionDigits: 3, maximumFractionDigits: 3})} contracts`;
                walletPositionValueSpan.innerHTML = `$${positionValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${formatProfitLoss(profitLoss)}`;
                walletTotalValueSpan.innerText = `$${totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                
                // Update checkbox state
                mockModeCheckbox.checked = !!data.mock_mode;
            })
            .catch(err => {
                writeTerminalLine(`Failed to load virtual wallet state: ${err.message}`, 'error');
            });
    }

    mockModeCheckbox.addEventListener('change', () => {
        const isChecked = mockModeCheckbox.checked;
        fetch(`/api/wallet/toggle-mock?enabled=${isChecked}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                writeTerminalLine(`✓ ${data.message}`, 'system');
            })
            .catch(err => {
                writeTerminalLine(`✗ Failed to update Sandbox mode: ${err.message}`, 'error');
                mockModeCheckbox.checked = !isChecked;
            });
    });

    loadFundsBtn.addEventListener('click', () => {
        const amount = parseFloat(loadAmountInput.value) || 10000.0;
        if (amount <= 0) {
            writeTerminalLine(`✗ Amount must be positive`, 'error');
            return;
        }
        loadFundsBtn.disabled = true;
        fetch(`/api/wallet/load?amount=${amount}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                loadFundsBtn.disabled = false;
                writeTerminalLine(`✓ SUCCESS: ${data.message}`, 'system');
                fetchWallet();
            })
            .catch(err => {
                loadFundsBtn.disabled = false;
                writeTerminalLine(`✗ Failed to load funds: ${err.message}`, 'error');
            });
    });

    // Wallet Modal toggling logic
    if (walletModalBtn && walletModal) {
        walletModalBtn.addEventListener('click', () => {
            walletModal.classList.add('open');
            fetchWallet();
        });
    }

    if (closeWalletBtn && walletModal) {
        closeWalletBtn.addEventListener('click', () => {
            walletModal.classList.remove('open');
        });
    }

    if (walletModal) {
        walletModal.addEventListener('click', (e) => {
            if (e.target === walletModal) {
                walletModal.classList.remove('open');
            }
        });
    }

    // Run fetchWallet on startup
    fetchWallet();

    // 1. Visual Theme Management (Dark/Light Persistence)
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);

    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });

    function setTheme(theme) {
        if (theme === 'dark') {
            body.classList.remove('light-theme');
            body.classList.add('dark-theme');
        } else {
            body.classList.remove('dark-theme');
            body.classList.add('light-theme');
        }
        localStorage.setItem('theme', theme);
    }



    // 2. Health Checker
    function checkHealth() {
        healthStatusDiv.className = 'health-badge checking';
        healthStatusDiv.querySelector('.status-label').innerText = 'Checking Connection...';
        
        fetch('/api/health')
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    healthStatusDiv.className = 'health-badge connected';
                    healthStatusDiv.querySelector('.status-label').innerText = 'Connected';
                    writeTerminalLine(`System connected to exchange: ${data.exchange}`, 'system');
                } else {
                    healthStatusDiv.className = 'health-badge error';
                    healthStatusDiv.querySelector('.status-label').innerText = 'Offline';
                    writeTerminalLine(`Exchange Connection Error: ${data.message || 'Unknown issue'}`, 'error');
                }
            })
            .catch(err => {
                healthStatusDiv.className = 'health-badge error';
                healthStatusDiv.querySelector('.status-label').innerText = 'Network Error';
                writeTerminalLine(`Local server unreachable: ${err.message}`, 'error');
            });
    }
    // Initial health check and check every 30 seconds
    checkHealth();
    setInterval(checkHealth, 30000);

    // 2b. Price Ticker Polling
    const tickerBadge = document.getElementById('symbol-price-ticker');
    let priceIntervalId = null;

    function fetchPrice() {
        const symbol = symbolInput.value.trim().toUpperCase();
        if (!symbol) {
            tickerBadge.innerText = 'Live: $--.--';
            return;
        }

        fetch(`/api/price/${symbol}`)
            .then(res => res.json())
            .then(data => {
                if (data.price && data.price > 0) {
                    const price = parseFloat(data.price);
                    const deviation = price * 0.05; // 5% deviation limit
                    
                    const priceStr = price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    const deviationStr = Math.floor(deviation).toLocaleString(undefined, {maximumFractionDigits: 0});
                    
                    tickerBadge.innerText = `Live: $${priceStr} ± ${deviationStr}`;

                    // Update Holding Value and Total Net Worth dynamically based on live price
                    const positionValue = currentPosition * price;
                    const totalValue = currentBalance + positionValue;
                    const profitLoss = totalValue - currentTotalDeposited;
                    
                    walletPositionValueSpan.innerHTML = `$${positionValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${formatProfitLoss(profitLoss)}`;
                    walletTotalValueSpan.innerText = `$${totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

                } else {
                    tickerBadge.innerText = 'Live: $--.--';
                }
            })
            .catch(() => {
                tickerBadge.innerText = 'Live: $--.--';
            });
    }

    function startPricePolling() {
        if (priceIntervalId) {
            clearInterval(priceIntervalId);
        }
        fetchPrice();
        priceIntervalId = setInterval(fetchPrice, 3000);
    }

    // Trigger price update when symbol changes
    symbolInput.addEventListener('input', () => {
        startPricePolling();
        fetchWallet();
    });

    // Run initial loaders on startup
    startPricePolling();




    // 3. Dynamic Inputs Based on Order Type

    function handleOrderTypeChange() {
        const orderType = orderTypeSelect.value;
        if (orderType === 'MARKET') {
            priceGroup.style.display = 'none';
            stopPriceGroup.style.display = 'none';
            priceInput.removeAttribute('required');
            stopPriceInput.removeAttribute('required');
        } else if (orderType === 'LIMIT') {
            priceGroup.style.display = 'flex';
            stopPriceGroup.style.display = 'none';
            priceInput.setAttribute('required', 'required');
            stopPriceInput.removeAttribute('required');
        } else if (orderType === 'STOP_LIMIT') {
            priceGroup.style.display = 'flex';
            stopPriceGroup.style.display = 'flex';
            priceInput.setAttribute('required', 'required');
            stopPriceInput.setAttribute('required', 'required');
        }
    }

    orderTypeSelect.addEventListener('change', handleOrderTypeChange);
    handleOrderTypeChange(); // Run once on startup

    // 4. Submit Button Theming based on Side Selection
    function updateSubmitButtonTheme() {
        const side = document.querySelector('input[name="side"]:checked').value;
        if (side === 'BUY') {
            submitBtn.className = 'submit-btn buy-theme';
            submitBtn.innerText = `Place BUY ${orderTypeSelect.value} Order`;
        } else {
            submitBtn.className = 'submit-btn sell-theme';
            submitBtn.innerText = `Place SELL ${orderTypeSelect.value} Order`;
        }
    }

    buyRadio.addEventListener('change', updateSubmitButtonTheme);
    sellRadio.addEventListener('change', updateSubmitButtonTheme);
    orderTypeSelect.addEventListener('change', updateSubmitButtonTheme);
    updateSubmitButtonTheme(); // Run once on startup

    // 5. Terminal Logger Function
    function writeTerminalLine(text, type = 'info') {
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        line.innerText = `[${timestamp}] ${text}`;
        
        terminalConsole.appendChild(line);
        // Auto scroll to bottom
        terminalConsole.scrollTop = terminalConsole.scrollHeight;
    }

    // 6. Handle Form Submission (AJAX Order Placement)
    orderForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const symbol = document.getElementById('symbol').value.trim().toUpperCase();
        const side = document.querySelector('input[name="side"]:checked').value;
        const orderType = orderTypeSelect.value;
        const quantity = parseFloat(document.getElementById('quantity').value);
        
        let price = null;
        let stopPrice = null;

        if (orderType === 'LIMIT' || orderType === 'STOP_LIMIT') {
            price = parseFloat(priceInput.value);
        }
        if (orderType === 'STOP_LIMIT') {
            stopPrice = parseFloat(stopPriceInput.value);
        }

        const payload = {
            symbol: symbol,
            side: side,
            order_type: orderType,
            quantity: quantity,
            price: price,
            stop_price: stopPrice
        };

        // UI state update
        submitBtn.disabled = true;
        const originalText = submitBtn.innerText;
        submitBtn.innerText = 'Executing order...';
        writeTerminalLine(`Sending request: ${side} ${orderType} of ${quantity} ${symbol}...`, 'info');

        fetch('/api/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(data => {
                    throw new Error(data.message || `HTTP error ${res.status}`);
                });
            }
            return res.json();
        })
        .then(data => {
            // Restore UI state
            submitBtn.disabled = false;
            submitBtn.innerText = originalText;
            
            if (data.success) {
                writeTerminalLine(`✓ SUCCESS: ${data.message} - ID: ${data.order_id} (Status: ${data.status})`, 'system');
                writeTerminalLine(`  Execution average price: $${data.avg_price}`, 'output');
                
                // Add order row to HTML table log
                addOrderToTable({
                    order_id: data.order_id,
                    symbol: data.symbol,
                    side: data.side,
                    order_type: data.order_type,
                    quantity: quantity,
                    price: price,
                    stop_price: stopPrice,
                    status: data.status || 'Success'
                });
            } else {
                writeTerminalLine(`✗ FAILED: ${data.message}`, 'error');
            }
            // Always refresh wallet state after attempting an order
            fetchWallet();
        })
        .catch(err => {
            // Restore UI state
            submitBtn.disabled = false;
            submitBtn.innerText = originalText;
            
            writeTerminalLine(`✗ EXCEPTION: ${err.message}`, 'error');
        });
    });

    // 7. Add order to the table log dynamically
    function addOrderToTable(order) {
        // Remove empty row if present
        const emptyRow = ordersTableBody.querySelector('.empty-row');
        if (emptyRow) {
            emptyRow.remove();
        }

        const row = document.createElement('tr');
        
        const sideClass = order.side.toLowerCase() === 'buy' ? 'buy' : 'sell';
        const statusClass = `status-${(order.status || '').toLowerCase()}`;

        row.innerHTML = `
            <td class="mono">${order.order_id || '-'}</td>
            <td>${order.symbol}</td>
            <td><span class="tag ${sideClass}">${order.side}</span></td>
            <td>${order.order_type}</td>
            <td class="mono">${order.quantity}</td>
            <td class="mono">${order.price ? '$' + order.price : '-'}</td>
            <td class="mono">${order.stop_price ? '$' + order.stop_price : '-'}</td>
            <td><span class="tag ${statusClass}">${order.status}</span></td>
        `;

        // Prepend new row to the table
        ordersTableBody.insertBefore(row, ordersTableBody.firstChild);
    }
});