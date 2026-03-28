const userModel = require('../Models/user.model');
const jwt = require('jsonwebtoken');
const emailService = require('../services/email.service');

const userRegister = async (req, res) => {
  try {
    const { email, password, name } = req.body;

    if (!email || !password || !name) {
      return res.status(400).json({ message: 'Email, password, and name are required' });
    }

    const isExists = await userModel.findOne({ email });
    if (isExists) {
      return res.status(400).json({ message: 'Email already exists' });
    }

    const user = await userModel.create({ email, password, name });

    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '3d' });

    res.cookie('token', token, { httpOnly: true });

    // Send email non-blocking (don't await before response)
    emailService.sendRegistrationEmail(user.email, user.name).catch(console.error);

    return res.status(201).json({
      message: 'User registered successfully',
      user: { id: user._id, email: user.email, name: user.name },
      token,
    });
  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
};

const userLogin = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ message: 'Email and password are required' });
    }

    const user = await userModel.findOne({ email }).select('+password');
    if (!user) {
      return res.status(400).json({ message: 'Invalid email or password' });
    }

    const isValidPassword = await user.comparePassword(password);
    if (!isValidPassword) {
      return res.status(400).json({ message: 'Invalid email or password' });
    }

    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '3d' });

    res.cookie('token', token, { httpOnly: true });

    return res.status(200).json({
      message: 'User logged in successfully',
      user: { id: user._id, email: user.email, name: user.name },
      token,
    });
  } catch (err) {
    return res.status(500).json({ message: err.message });
  }
};

module.exports = { userRegister, userLogin };
