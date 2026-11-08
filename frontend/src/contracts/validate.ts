import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import schema from "../../../contracts/public-event.schema.json";
import type { PublicEvent } from "./public-event";
const ajv = new Ajv2020({ strict: false, coerceTypes: false, removeAdditional: false });
addFormats(ajv);
const validate = ajv.compile<PublicEvent>(schema);
export function parsePublicEvent(input: unknown): PublicEvent {
  if (!validate(input)) throw new Error("Invalid public event");
  return input;
}
