const accountModel = require('../Models/account.model');
const transactionModel = require('../Models/transactions.models');

async function createAccount(req, res) {
  try {
    const user = req.user;
    const account = await accountModel.create({ user: user._id });
    return res.status(201).json({ message: 'Account created successfully', account });
  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
}

async function getAccounts(req, res) {
  try {
    const accounts = await accountModel.find({ user: req.user._id }).populate('user', 'name email');

    // Attach live balance to each account
    const accountsWithBalance = await Promise.all(
      accounts.map(async (acc) => {
        const balance = await acc.getBalance();
        return { ...acc.toObject(), balance };
      })
    );

    return res.status(200).json({ accounts: accountsWithBalance });
  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
}

async function getAccountBalance(req, res) {
  try {
    const { accountId } = req.params;
    const account = await accountModel.findOne({ _id: accountId, user: req.user._id });
    if (!account) {
      return res.status(404).json({ message: 'Account not found' });
    }
    const balance = await account.getBalance();
    return res.status(200).json({ balance });
  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
}

async function getAccountTransactions(req, res) {
  try {
    const { accountId } = req.params;
    const account = await accountModel.findOne({ _id: accountId, user: req.user._id });
    if (!account) {
      return res.status(404).json({ message: 'Account not found' });
    }

    const transactions = await transactionModel.find({
      $or: [{ fromAccount: account._id }, { toAccount: account._id }],
    })
      .sort({ createdAt: -1 })
      .populate('fromAccount', 'user currency')
      .populate('toAccount', 'user currency');

    return res.status(200).json({ transactions });
  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
}

async function getAllAccounts(req, res) {
  try {
    const accounts = await accountModel.find().populate('user', 'name email');

    const accountsWithBalance = await Promise.all(
      accounts.map(async (acc) => {
        const balance = await acc.getBalance();
        return { ...acc.toObject(), balance };
      })
    );

    res.status(200).json({ accounts: accountsWithBalance });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
}

async function depositBalance(req, res) {
  const mongoose = require('mongoose');
  const ledgerModel = require('../Models/ledger.model');
  const transactionModel = require('../Models/transactions.models');

  try {
    const { amount } = req.body;

    if (!amount || isNaN(amount) || Number(amount) <= 0) {
      return res.status(400).json({ message: 'Amount must be a positive number' });
    }

    const account = await accountModel.findOne({ user: req.user._id, status: 'active' });
    if (!account) {
      return res.status(404).json({ message: 'Active account not found' });
    }

    const idempotencyKey = `deposit-${req.user._id}-${Date.now()}`;

    const session = await mongoose.startSession();
    session.startTransaction();

    try {
      const transaction = new transactionModel({
        fromAccount: account._id,
        toAccount: account._id,
        amount: Number(amount),
        idempotencyKey,
        status: 'pending',
      });
      await transaction.save({ session });

      await ledgerModel.create([{
        account: account._id,
        transaction: transaction._id,
        type: 'credit',
        amount: Number(amount),
      }], { session });

      transaction.status = 'completed';
      await transaction.save({ session });

      await session.commitTransaction();
      session.endSession();

      const newBalance = await account.getBalance();
      return res.status(200).json({ message: 'Balance added successfully', balance: newBalance });
    } catch (err) {
      await session.abortTransaction();
      session.endSession();
      throw err;
    }
  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
}

module.exports = {
  createAccount,
  getAccounts,
  getAccountBalance,
  getAccountTransactions,
  getAllAccounts,
  depositBalance,
};
