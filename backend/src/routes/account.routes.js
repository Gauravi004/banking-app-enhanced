const express = require('express');
const { authMiddleware } = require('../middleware/auth.middleware');
const accountController = require('../controllers/account.controller');
const router = express.Router();

router.post('/', authMiddleware, accountController.createAccount);
router.get('/', authMiddleware, accountController.getAccounts);
router.get('/balance/:accountId', authMiddleware, accountController.getAccountBalance);
router.get('/transactions/:accountId', authMiddleware, accountController.getAccountTransactions);
router.get('/all', authMiddleware, accountController.getAllAccounts);
router.post('/deposit', authMiddleware, accountController.depositBalance);

module.exports = router;
