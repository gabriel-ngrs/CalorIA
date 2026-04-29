const toast = {
  success: jest.fn(),
  error: jest.fn(),
  info: jest.fn(),
  warning: jest.fn(),
  promise: jest.fn(),
  dismiss: jest.fn(),
};

module.exports = { toast };
