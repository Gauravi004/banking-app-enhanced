require('dotenv').config();
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    type: 'OAuth2',
    user: process.env.EMAIL_USER,
    clientId: process.env.CLIENT_ID,
    clientSecret: process.env.CLIENT_SECRET,
    refreshToken: process.env.REFRESH_TOKEN,
  },
});

transporter.verify((error) => {
  if (error) {
    console.error('Error connecting to email server:', error);
  } else {
    console.log('Email server is ready to send messages');
  }
});

const sendEmail = async (to, subject, text, html) => {
  try {
    const info = await transporter.sendMail({
      from: `"Banking App" <${process.env.EMAIL_USER}>`,
      to,
      subject,
      text,
      html,
    });
    console.log('Message sent:', info.messageId);
  } catch (error) {
    console.error('Error sending email:', error);
  }
};

async function sendRegistrationEmail(userEmail, userName) {
  const subject = 'Welcome to Our Banking App!';
  const text = `Hi ${userName},\n\nThank you for registering! Your account has been created successfully.\n\nBest regards,\nThe Team`;
  const html = `<p>Hi ${userName},</p><p>Thank you for registering! Your account has been created successfully.</p><p>Best regards,<br>The Team</p>`;
  await sendEmail(userEmail, subject, text, html);
}

// FIX: Renamed from sendtransactionEmail → sendTransactionEmail (capital T)
// to match what transaction.controller.js calls
async function sendTransactionEmail(userEmail, userName, amount, toAccount) {
  const subject = 'Transaction Successful';
  const text = `Hi ${userName},\n\nYour transaction of ₹${amount} to account ${toAccount} was successful!\n\nBest regards,\nThe Team`;
  const html = `<p>Hi ${userName},</p><p>Your transaction of <strong>₹${amount}</strong> to account <strong>${toAccount}</strong> was successful!</p><p>Best regards,<br>The Team</p>`;
  await sendEmail(userEmail, subject, text, html);
}

async function sendTransactionFailureEmail(userEmail, userName, amount, toAccount) {
  const subject = 'Transaction Failed';
  const text = `Hi ${userName},\n\nYour transaction of ₹${amount} to account ${toAccount} failed.\n\nBest regards,\nThe Team`;
  const html = `<p>Hi ${userName},</p><p>Your transaction of <strong>₹${amount}</strong> to account <strong>${toAccount}</strong> failed.</p><p>Best regards,<br>The Team</p>`;
  await sendEmail(userEmail, subject, text, html);
}

module.exports = {
  sendRegistrationEmail,
  sendTransactionEmail,
  sendTransactionFailureEmail,
};
