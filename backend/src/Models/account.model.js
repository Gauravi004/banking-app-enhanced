const mongoose = require('mongoose');
const ledgerModel = require('./ledger.model');

const accountSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true,
  },
  status: {
    type: String,
    enum: {
      values: ['active', 'frozen', 'inactive'],
      message: 'Status must be either active, frozen, or inactive',
    },
    default: 'active',
  },
  currency: {
    type: String,
    required: [true, 'Currency is required'],
    default: 'INR',
  },
}, { timestamps: true });

// FIX: Removed unique compound index on {user, status} — it prevented
// a user from ever having more than one account of the same status.
accountSchema.index({ user: 1 });

accountSchema.methods.getBalance = async function () {
  const balanceData = await ledgerModel.aggregate([
    { $match: { account: this._id } },
    {
      $group: {
        _id: null,
        totalDebit: { $sum: { $cond: [{ $eq: ['$type', 'debit'] }, '$amount', 0] } },
        totalCredit: { $sum: { $cond: [{ $eq: ['$type', 'credit'] }, '$amount', 0] } },
      },
    },
    { $project: { _id: 0, balance: { $subtract: ['$totalCredit', '$totalDebit'] } } },
  ]);

  if (balanceData.length === 0) return 0;
  return balanceData[0].balance;
};

const accountModel = mongoose.model('Account', accountSchema);
module.exports = accountModel;
