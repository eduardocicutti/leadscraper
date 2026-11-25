import pkg from "../package.json";
import { PRODUTO } from "./config/produto";

export const APP_NAME = PRODUTO.nome;
export const APP_VERSION = pkg.version;
export const APP_TITLE = `${APP_NAME} ${APP_VERSION}`;
