const mongoose = require('mongoose');
const transactionModel = require('../Models/transactions.models');
const ledgerModel = require('../Models/ledger.model');
const emailService = require('../services/email.service');
const accountModel = require('../Models/account.model');

// Regular peer-to-peer transfer between two accounts
async function createTransaction(req, res) {
  try {
    const { toAccountId, amount, idempotencyKey } = req.body;

    if (!toAccountId || !amount || !idempotencyKey) {
      return res.status(400).json({ message: 'toAccountId, amount, and idempotencyKey are required' });
    }

    if (!mongoose.Types.ObjectId.isValid(toAccountId)) {
      return res.status(400).json({ message: 'Invalid toAccountId' });
    }

    if (amount <= 0) {
      return res.status(400).json({ message: 'Amount must be greater than 0' });
    }

    // Idempotency check
    const existing = await transactionModel.findOne({ idempotencyKey });
    if (existing) {
      return res.status(200).json({
        message: `Transaction already exists with status: ${existing.status}`,
        transaction: existing,
      });
    }

    const fromAccount = await accountModel.findOne({ user: req.user._id, status: 'active' });
    if (!fromAccount) {
      return res.status(404).json({ message: 'Your active account was not found' });
    }

    const toAccount = await accountModel.findOne({ _id: toAccountId, status: 'active' });
    if (!toAccount) {
      return res.status(404).json({ message: 'Recipient account not found' });
    }

    if (fromAccount._id.equals(toAccount._id)) {
      return res.status(400).json({ message: 'Cannot transfer to the same account' });
    }

    const balance = await fromAccount.getBalance();
    if (balance < amount) {
      return res.status(400).json({
        message: `Insufficient balance. Available: ₹${balance}, Required: ₹${amount}`,
      });
    }

    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const transaction = new transactionModel({
        fromAccount: fromAccount._id,
        toAccount: toAccount._id,
        amount,
        idempotencyKey,
        status: 'pending',
      });
      await transaction.save({ session });

      await ledgerModel.create([{
        account: fromAccount._id,
        transaction: transaction._id,
        type: 'debit',
        amount,
      }], { session });

      await ledgerModel.create([{
        account: toAccount._id,
        transaction: transaction._id,
        type: 'credit',
        amount,
      }], { session });

      transaction.status = 'completed';
      await transaction.save({ session });

      await session.commitTransaction();
      session.endSession();

      // Non-blocking email
      emailService.sendTransactionEmail(req.user.email, req.user.name, amount, toAccount._id).catch(console.error);

      return res.status(201).json({ message: 'Transaction successful', transaction });
    } catch (err) {
      await session.abortTransaction();
      session.endSession();
      throw err;
    }
  } catch (error) {
    console.error('Transaction Error:', error);
    return res.status(500).json({ message: 'Internal server error', error: error.message });
  }
}

// System admin endpoint: deposit initial funds into any user's account
async function createInitialFundsTransaction(req, res) {
  try {
    const { toaccount, amount, idempotencyKey } = req.body;

    if (!toaccount || !amount || !idempotencyKey) {
      return res.status(400).json({ message: 'toaccount (user ID), amount, and idempotencyKey are required' });
    }

    if (!mongoose.Types.ObjectId.isValid(toaccount)) {
      return res.status(400).json({ message: 'Invalid account/user id' });
    }

    const ToUserAccount = await accountModel.findOne({ user: toaccount, status: 'active' });
    if (!ToUserAccount) {
      return res.status(404).json({ message: 'Recipient account not found' });
    }

    const fromUserAccount = await accountModel.findOne({ user: req.user._id, status: 'active' });
    if (!fromUserAccount) {
      return res.status(404).json({ message: 'Sender account not found' });
    }

    const existing = await transactionModel.findOne({ idempotencyKey });
    if (existing) {
      return res.status(200).json({
        message: `Transaction already exists with status: ${existing.status}`,
        transaction: existing,
      });
    }

    const balance = await fromUserAccount.getBalance();
    if (balance < amount) {
      return res.status(400).json({
        message: `Insufficient balance. Available: ₹${balance}, Required: ₹${amount}`,
      });
    }

    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const transaction = new transactionModel({
        fromAccount: fromUserAccount._id,
        toAccount: ToUserAccount._id,
        amount,
        idempotencyKey,
        status: 'pending',
      });
      await transaction.save({ session });

      await ledgerModel.create([{
        account: fromUserAccount._id,
        transaction: transaction._id,
        type: 'debit',
        amount,
      }], { session });

      await ledgerModel.create([{
        account: ToUserAccount._id,
        transaction: transaction._id,
        type: 'credit',
        amount,
      }], { session });

      transaction.status = 'completed';
      await transaction.save({ session });

      await session.commitTransaction();
      session.endSession();

      // FIX: was emailService.sendTransactionEmail (now correctly named)
      emailService.sendTransactionEmail(req.user.email, req.user.name, amount, ToUserAccount._id).catch(console.error);

      return res.status(201).json({ message: 'Initial funds transaction successful', transaction });
    } catch (err) {
      await session.abortTransaction();
      session.endSession();
      throw err;
    }
  } catch (error) {
    console.error('Transaction Error:', error);
    return res.status(500).json({ message: 'Internal server error', error: error.message });
  }
}

module.exports = { createTransaction, createInitialFundsTransaction };
