const mongoose = require('mongoose');

function connectDB() {
  mongoose.connect(process.env.MONGO_URI)
    .then(() => console.log('Connected to database'))
    .catch((err) => {
      console.error('Error connecting to database:', err);
      process.exit(1);
    });
}

module.exports = connectDB;
