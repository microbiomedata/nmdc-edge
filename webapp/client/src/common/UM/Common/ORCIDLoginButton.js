import { createButton } from "react-social-login-buttons";

const config = {
  text: "Login with ORCiD",
  icon: '',
  iconFormat: name => `fa fa-${name}`,
  style: { background: "#A5DF00", color: "white" },
  activeStyle: { background: "#86B404" }
};

const ORCIDLoginButton = createButton(config);

export default ORCIDLoginButton;