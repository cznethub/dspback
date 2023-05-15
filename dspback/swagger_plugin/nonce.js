  /**
   * Issue a random nonce value.
   *
   * https://stackoverflow.com/a/1349426
   */
  function randomNonce() {
    var result = "";
    var characters =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    var charactersLength = characters.length;
    for (var i = 0; i < 10; i++) {
      result += characters.charAt(
        Math.floor(Math.random() * charactersLength)
      );
    }
    return result;
  }

  /**
   * Fix OpenID request parameters.
   *
   * According to the specification [1], the authorize request for an OpenID Implicit flow MUST contain
   * either "id_token" or "id_token token", but SwaggerUI only uses "token" which actually matches an
   * OAuth2 (not OpenID) Implicit flow.
   *
   * The second patch is for the nonce parameter that MUST be present in a Implicit flow request [2]. This
   * plugin does NOT validate that nonce value at redirect matches the initially issued. To do so, we'd need
   * to store it at the localStorage to later check at the redirect URL.
   *
   * This code is inspired by [3], mentioned at [4]
   *
   * [1] https://openid.net/specs/openid-connect-core-1_0.html#rfc.section.3
   * [2] https://openid.net/specs/openid-connect-core-1_0.html#rfc.section.3.2.2.1
   * [3] https://github.com/inouiw/SwaggerUIJsonWebToken/blob/master/wwwroot/swagger-extensions/my-swagger-ui-plugins.js
   * [4] https://github.com/swagger-api/swagger-ui/issues/7698
   */
  const OpenIdImplicitFlowFix = function (system) {
    return {
      statePlugins: {
        auth: {
          wrapActions: {
            // Called when you click in the 'Authorize' in the Authorize pop-up.
            authPopup:
              (oriAction, system) => (url, swaggerUIRedirectOauth2) => {
                const nonce = randomNonce();
                const newUrl = url.replace(
                  "response_type=token",
                  `response_type=token+id_token&nonce=${nonce}`
                );
                console.log(`authPopup wrapAction. new url: ${newUrl}`);
                return oriAction(newUrl, swaggerUIRedirectOauth2);
              },
          },
        },
      },
    };
  };